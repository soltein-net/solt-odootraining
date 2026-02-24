#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente JSON-RPC para solt_library
=====================================

Este script demuestra cómo interactuar con el módulo solt_library usando JSON-RPC.
JSON-RPC es el protocolo nativo de la interfaz web de Odoo y ofrece mayor flexibilidad.

Casos de uso implementados:
1. Dashboard estadístico de la biblioteca (conteos globales por estado)
2. Registro de nuevo socio con datos completos
3. Búsqueda avanzada de libros con paginación
4. Exportación completa del catálogo con autores y categorías
5. Consulta de préstamos vencidos con detalle de multas
6. Uso del Context: multi-empresa, idioma/traducciones y registros archivados

Modelos utilizados:
- library.book     : Catálogo de libros
- library.loan     : Préstamos activos e históricos
- library.member   : Socios registrados de la biblioteca
- library.author   : Autores del catálogo
- library.category : Categorías bibliográficas

Autor: Soltein Training
Fecha: 2026
"""

import json
import logging
import random
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Configuración de logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('jsonrpc_library.log'),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ── Cliente JSON-RPC base ─────────────────────────────────────────────────────

class OdooJSONRPCClient:
    """
    Cliente JSON-RPC avanzado para Odoo 17.
    Incluye retry automático con backoff, manejo de errores estructurado
    y soporte para operaciones en lote (batch).
    """

    def __init__(
        self,
        server_url: str,
        database_name: str,
        username: str,
        api_key: str,
        request_timeout_seconds: int = 30,
        max_retry_attempts: int = 3,
    ):
        self.server_url = server_url.rstrip('/')
        self.database_name = database_name
        self.username = username
        self.api_key = api_key
        self.request_timeout_seconds = request_timeout_seconds
        self.authenticated_user_id: Optional[int] = None

        self.jsonrpc_endpoint = f'{self.server_url}/jsonrpc'

        # Sesión HTTP con retry automático
        self.http_session = requests.Session()
        retry_strategy = Retry(
            total=max_retry_attempts,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=['POST'],
            backoff_factor=1,
        )
        http_adapter = HTTPAdapter(max_retries=retry_strategy)
        self.http_session.mount('http://', http_adapter)
        self.http_session.mount('https://', http_adapter)

        self.default_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'SolteinLibraryClient/1.0',
        }

        logger.info(f'Cliente JSON-RPC inicializado para {server_url}')

    def _generate_request_id(self) -> int:
        """Genera un ID único para identificar cada petición JSON-RPC."""
        return random.randint(1, 10_000_000)

    def _build_jsonrpc_payload(
        self,
        service_name: str,
        method_name: str,
        *method_args,
    ) -> str:
        """
        Construye el payload JSON-RPC 2.0 estándar.

        Args:
            service_name: Servicio de Odoo ('common' o 'object').
            method_name:  Método del servicio a invocar.
            *method_args: Argumentos del método.

        Returns:
            Cadena JSON serializada lista para enviar.
        """
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'service': service_name,
                'method': method_name,
                'args': list(method_args),
            },
            'id': self._generate_request_id(),
        }
        return json.dumps(payload)

    def _send_request(self, json_payload: str) -> Dict:
        """
        Envía una petición HTTP POST al endpoint JSON-RPC de Odoo.

        Args:
            json_payload: Cuerpo JSON serializado de la petición.

        Returns:
            Diccionario con la respuesta JSON-RPC del servidor.

        Raises:
            RuntimeError: Si la respuesta contiene un error JSON-RPC.
            requests.RequestException: Si hay un problema de red.
        """
        try:
            http_response = self.http_session.post(
                self.jsonrpc_endpoint,
                data=json_payload,
                headers=self.default_headers,
                timeout=self.request_timeout_seconds,
            )
            http_response.raise_for_status()

            parsed_response = http_response.json()

            if 'error' in parsed_response:
                error_details = parsed_response['error']
                error_message = (
                    f"JSON-RPC Error [{error_details.get('code')}]: "
                    f"{error_details.get('message', 'Error desconocido')}"
                )
                if 'data' in error_details:
                    error_message += f" — {error_details['data']}"
                raise RuntimeError(error_message)

            return parsed_response

        except requests.RequestException as network_error:
            logger.error(f'Error de red: {network_error}')
            raise
        except json.JSONDecodeError as parse_error:
            logger.error(f'Error parseando respuesta JSON: {parse_error}')
            raise

    def authenticate(self) -> bool:
        """
        Autentica al usuario y almacena el user_id para peticiones posteriores.

        Returns:
            bool: True si la autenticación fue exitosa.
        """
        try:
            version_payload = self._build_jsonrpc_payload('common', 'version')
            version_response = self._send_request(version_payload)

            if 'result' in version_response:
                server_version = version_response['result'].get(
                    'server_version', 'desconocida'
                )
                logger.info(f'Conectado a Odoo {server_version}')

            auth_payload = self._build_jsonrpc_payload(
                'common', 'login',
                self.database_name,
                self.username,
                self.api_key,
            )
            auth_response = self._send_request(auth_payload)

            self.authenticated_user_id = auth_response.get('result')

            if self.authenticated_user_id:
                logger.info(
                    f'Autenticación exitosa. User ID: {self.authenticated_user_id}'
                )
                return True

            logger.error('Autenticación fallida: credenciales incorrectas')
            return False

        except Exception as authentication_error:
            logger.error(f'Error durante autenticación: {authentication_error}')
            return False

    def execute_kw(
        self,
        model_name: str,
        method_name: str,
        positional_args: List = None,
        keyword_args: Dict = None,
    ) -> Any:
        """
        Invoca execute_kw sobre cualquier modelo de Odoo vía JSON-RPC.

        Args:
            model_name:      Nombre técnico del modelo.
            method_name:     Método ORM a invocar.
            positional_args: Argumentos posicionales del método.
            keyword_args:    Argumentos con nombre del método.

        Returns:
            El resultado del método remoto.

        Raises:
            RuntimeError: Si el usuario no está autenticado.
        """
        if not self.authenticated_user_id:
            raise RuntimeError(
                'Usuario no autenticado. Llama a authenticate() primero.'
            )

        positional_args = positional_args or []
        keyword_args = keyword_args or {}

        rpc_payload = self._build_jsonrpc_payload(
            'object', 'execute_kw',
            self.database_name,
            self.authenticated_user_id,
            self.api_key,
            model_name,
            method_name,
            positional_args,
            keyword_args,
        )

        try:
            rpc_response = self._send_request(rpc_payload)
            return rpc_response.get('result')
        except Exception as execution_error:
            logger.error(
                f'Error ejecutando {model_name}.{method_name}: {execution_error}'
            )
            raise

    def batch_execute(self, operation_list: List[Dict]) -> List[Any]:
        """
        Ejecuta múltiples operaciones en una sola petición HTTP (batch).

        Args:
            operation_list: Lista de dicts con keys 'model', 'method',
                            'args' (opcional) y 'kwargs' (opcional).

        Returns:
            Lista de resultados en el mismo orden que las operaciones.
        """
        if not self.authenticated_user_id:
            raise RuntimeError('Usuario no autenticado.')

        # Se envía cada operación como request individual y se acumulan resultados.
        ordered_results = []
        for operation_index, operation in enumerate(operation_list):
            single_payload = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'service': 'object',
                    'method': 'execute_kw',
                    'args': [
                        self.database_name,
                        self.authenticated_user_id,
                        self.api_key,
                        operation['model'],
                        operation['method'],
                        operation.get('args', []),
                        operation.get('kwargs', {}),
                    ],
                },
                'id': operation_index,
            }

            try:
                single_response = self.http_session.post(
                    self.jsonrpc_endpoint,
                    data=json.dumps(single_payload),
                    headers=self.default_headers,
                    timeout=self.request_timeout_seconds,
                )
                single_response.raise_for_status()
                response_body = single_response.json()

                if 'error' in response_body:
                    logger.error(
                        f"Error en operación {operation_index}: "
                        f"{response_body['error']}"
                    )
                    ordered_results.append({'error': response_body['error']})
                else:
                    ordered_results.append(response_body.get('result'))

            except Exception as operation_error:
                logger.error(
                    f'Error en batch execution: {operation_error}'
                )
                raise

        return ordered_results


# ── Gestor especializado para solt_library ────────────────────────────────────

class LibraryJSONRPCManager:
    """
    Gestor de operaciones de la biblioteca vía JSON-RPC.
    Aprovecha batch execution y búsqueda avanzada con paginación.
    """

    BOOK_MODEL = 'library.book'
    LOAN_MODEL = 'library.loan'
    MEMBER_MODEL = 'library.member'
    AUTHOR_MODEL = 'library.author'
    CATEGORY_MODEL = 'library.category'

    def __init__(self, client: OdooJSONRPCClient):
        self.client = client

    # ── Caso de uso 1: Dashboard estadístico ─────────────────────────────────

    def get_library_dashboard(self) -> Dict:
        """
        Obtiene estadísticas globales de la biblioteca en una sola pasada.
        Usa batch execution para reducir la latencia de red.

        Returns:
            Diccionario con conteos por estado de libros, préstamos y socios,
            más los préstamos vencidos y libros de mayor demanda.
        """
        logger.info('=== CASO 1: Dashboard estadístico de la biblioteca ===')

        # Ejecutar todas las consultas de conteo en batch
        count_operations = [
            # Libros por estado
            {'model': self.BOOK_MODEL, 'method': 'search_count',
             'args': [[('state', '=', 'available')]]},
            {'model': self.BOOK_MODEL, 'method': 'search_count',
             'args': [[('state', '=', 'low_stock')]]},
            {'model': self.BOOK_MODEL, 'method': 'search_count',
             'args': [[('state', '=', 'unavailable')]]},
            # Préstamos por estado
            {'model': self.LOAN_MODEL, 'method': 'search_count',
             'args': [[('state', '=', 'loaned')]]},
            {'model': self.LOAN_MODEL, 'method': 'search_count',
             'args': [[('state', '=', 'returned')]]},
            {'model': self.LOAN_MODEL, 'method': 'search_count',
             'args': [[('state', '=', 'lost')]]},
            # Socios por estado
            {'model': self.MEMBER_MODEL, 'method': 'search_count',
             'args': [[('state', '=', 'active')]]},
            {'model': self.MEMBER_MODEL, 'method': 'search_count',
             'args': [[('state', '=', 'suspended')]]},
            {'model': self.MEMBER_MODEL, 'method': 'search_count',
             'args': [[('state', '=', 'expired')]]},
            # Préstamos vencidos (activos con días de retraso)
            {'model': self.LOAN_MODEL, 'method': 'search_count',
             'args': [[('state', '=', 'loaned'), ('days_overdue', '>', 0)]]},
        ]

        batch_counts = self.client.batch_execute(count_operations)

        # Préstamos recientes (consulta individual para incluir campos)
        recent_loans = self.client.execute_kw(
            self.LOAN_MODEL,
            'search_read',
            [[]],
            {
                'fields': [
                    'reference', 'book_id', 'member_id', 'state',
                    'loan_date', 'expected_return_date', 'days_overdue',
                ],
                'limit': 5,
                'order': 'loan_date desc',
            },
        )

        library_dashboard = {
            'books': {
                'available': batch_counts[0],
                'low_stock': batch_counts[1],
                'unavailable': batch_counts[2],
                'total': (batch_counts[0] or 0)
                         + (batch_counts[1] or 0)
                         + (batch_counts[2] or 0),
            },
            'loans': {
                'active': batch_counts[3],
                'returned': batch_counts[4],
                'lost': batch_counts[5],
                'overdue': batch_counts[9],
            },
            'members': {
                'active': batch_counts[6],
                'suspended': batch_counts[7],
                'expired': batch_counts[8],
                'total': (batch_counts[6] or 0)
                         + (batch_counts[7] or 0)
                         + (batch_counts[8] or 0),
            },
            'recent_loans': recent_loans,
            'generated_at': datetime.now().isoformat(),
        }

        logger.info('Dashboard generado exitosamente:')
        logger.info(
            f"  Libros — Disponibles: {library_dashboard['books']['available']} | "
            f"Stock bajo: {library_dashboard['books']['low_stock']} | "
            f"No disponibles: {library_dashboard['books']['unavailable']}"
        )
        logger.info(
            f"  Préstamos — Activos: {library_dashboard['loans']['active']} | "
            f"Vencidos: {library_dashboard['loans']['overdue']} | "
            f"Perdidos: {library_dashboard['loans']['lost']}"
        )
        logger.info(
            f"  Socios — Activos: {library_dashboard['members']['active']} | "
            f"Total: {library_dashboard['members']['total']}"
        )

        return library_dashboard

    # ── Caso de uso 2: Registro de nuevo socio ────────────────────────────────

    def register_new_member(
        self,
        full_name: str,
        email_address: str,
        phone_number: str,
        membership_type: str = 'regular',
        street_address: str = '',
    ) -> Optional[int]:
        """
        Registra un nuevo socio en la biblioteca creando el registro library.member.
        El modelo usa _inherits sobre res.partner, por lo que los datos del
        contacto se crean automáticamente.

        Args:
            full_name:       Nombre completo del socio.
            email_address:   Correo electrónico de contacto.
            phone_number:    Teléfono de contacto.
            membership_type: Tipo de membresía ('student', 'regular', 'premium', 'lifetime').
            street_address:  Dirección física (opcional).

        Returns:
            ID del nuevo miembro creado, o None si falla.
        """
        logger.info('=== CASO 2: Registro de nuevo socio ===')
        logger.info(
            f'Registrando: {full_name} — Tipo: {membership_type}'
        )

        valid_membership_types = ('student', 'regular', 'premium', 'lifetime')
        if membership_type not in valid_membership_types:
            logger.error(
                f"Tipo de membresía inválido: '{membership_type}'. "
                f"Opciones válidas: {valid_membership_types}"
            )
            return None

        # Crear el miembro (el _inherits crea el res.partner automáticamente)
        new_member_id = self.client.execute_kw(
            self.MEMBER_MODEL,
            'create',
            [{
                'name': full_name,
                'email': email_address,
                'phone': phone_number,
                'street': street_address,
                'membership_type': membership_type,
                'registration_date': datetime.today().strftime('%Y-%m-%d'),
            }],
        )

        if not new_member_id:
            logger.error('No se pudo crear el socio')
            return None

        # Leer el registro creado para confirmar y obtener el código asignado
        created_member_data_list = self.client.execute_kw(
            self.MEMBER_MODEL,
            'read',
            [[new_member_id]],
            {
                'fields': [
                    'name', 'code', 'membership_type',
                    'max_loans', 'loan_days', 'expiration_date', 'state',
                ],
            },
        )

        created_member_data = created_member_data_list[0]
        logger.info(
            f"Socio registrado — Código: {created_member_data['code']} | "
            f"Tipo: {created_member_data['membership_type']} | "
            f"Máx. préstamos: {created_member_data['max_loans']} | "
            f"Días por préstamo: {created_member_data['loan_days']} | "
            f"Vence: {created_member_data['expiration_date']}"
        )

        return new_member_id

    # ── Caso de uso 3: Búsqueda avanzada con paginación ───────────────────────

    def search_books_with_pagination(
        self,
        search_filters: Dict,
        page_number: int = 1,
        page_size: int = 10,
        sort_field: str = 'name',
        sort_direction: str = 'asc',
    ) -> Dict:
        """
        Realiza búsqueda avanzada de libros con paginación completa.

        Args:
            search_filters: Diccionario de filtros, p. ej.:
                            {'state': 'available', 'language': 'es'}
                            También acepta {'category_id': 3, 'publisher': 'Planeta'}.
            page_number:    Número de página (empezando en 1).
            page_size:      Registros por página.
            sort_field:     Campo para ordenar.
            sort_direction: 'asc' o 'desc'.

        Returns:
            Dict con 'books', 'total_books', 'total_pages',
            'current_page' y 'has_next_page'.
        """
        logger.info('=== CASO 3: Búsqueda avanzada con paginación ===')

        # Construir dominio dinámico desde el diccionario de filtros
        search_domain = []
        for field_name, filter_value in search_filters.items():
            if isinstance(filter_value, list):
                search_domain.append((field_name, 'in', filter_value))
            elif isinstance(filter_value, dict) and 'operator' in filter_value:
                search_domain.append(
                    (field_name, filter_value['operator'], filter_value['value'])
                )
            else:
                search_domain.append((field_name, '=', filter_value))

        logger.info(f'Dominio: {search_domain} — Página {page_number} (tamaño {page_size})')

        page_offset = (page_number - 1) * page_size

        # Contar total antes de paginar
        total_books_count = self.client.execute_kw(
            self.BOOK_MODEL,
            'search_count',
            [search_domain],
        )

        # Obtener página de resultados
        page_books = self.client.execute_kw(
            self.BOOK_MODEL,
            'search_read',
            [search_domain],
            {
                'fields': [
                    'id', 'name', 'isbn', 'author_ids', 'category_id',
                    'language', 'available_qty', 'total_qty', 'state',
                    'publisher', 'publication_date', 'pages',
                ],
                'offset': page_offset,
                'limit': page_size,
                'order': f'{sort_field} {sort_direction}',
            },
        )

        import math
        total_pages = math.ceil(total_books_count / page_size) if page_size > 0 else 1

        pagination_result = {
            'books': page_books,
            'total_books': total_books_count,
            'total_pages': total_pages,
            'current_page': page_number,
            'has_next_page': page_number < total_pages,
        }

        logger.info(
            f'Resultados: {len(page_books)} libro(s) en página {page_number}/{total_pages} '
            f'(total: {total_books_count})'
        )
        for book_record in page_books:
            logger.info(
                f"  • [{book_record['id']}] {book_record['name']} "
                f"— {book_record['category_id'][1] if book_record['category_id'] else 'Sin categoría'} "
                f"— Disp: {book_record['available_qty']}/{book_record['total_qty']}"
            )

        return pagination_result

    # ── Caso de uso 4: Exportación del catálogo ───────────────────────────────

    def export_full_catalog(self, include_unavailable: bool = False) -> List[Dict]:
        """
        Exporta el catálogo completo de libros con sus autores y categoría.
        Diseñado para integraciones B2B o sistemas de Data Warehousing.

        Args:
            include_unavailable: Si True, incluye libros sin stock.

        Returns:
            Lista de dicts enriquecidos con nombre de autores y categoría.
        """
        logger.info('=== CASO 4: Exportación completa del catálogo ===')

        export_domain = [] if include_unavailable else [('state', '!=', 'unavailable')]

        all_books = self.client.execute_kw(
            self.BOOK_MODEL,
            'search_read',
            [export_domain],
            {
                'fields': [
                    'id', 'name', 'isbn', 'author_ids', 'category_id',
                    'language', 'publisher', 'publication_date',
                    'total_qty', 'available_qty', 'state',
                    'description', 'pages',
                ],
                'order': 'name asc',
                'limit': 2000,  # Límite de exportación
            },
        )

        if not all_books:
            logger.warning('No se encontraron libros para exportar')
            return []

        # Obtener todos los autores únicos en una sola consulta
        all_author_ids = list({
            author_id
            for book_record in all_books
            for author_id in book_record.get('author_ids', [])
        })

        author_details_by_id: Dict[int, str] = {}
        if all_author_ids:
            author_records = self.client.execute_kw(
                self.AUTHOR_MODEL,
                'read',
                [all_author_ids],
                {'fields': ['id', 'name', 'nationality']},
            )
            author_details_by_id = {
                author_record['id']: author_record['name']
                for author_record in author_records
            }

        # Enriquecer cada libro con nombres de autores legibles
        enriched_catalog = []
        for book_record in all_books:
            author_names = [
                author_details_by_id.get(author_id, f'ID:{author_id}')
                for author_id in book_record.get('author_ids', [])
            ]

            enriched_book = {
                'id': book_record['id'],
                'title': book_record['name'],
                'isbn': book_record.get('isbn', ''),
                'authors': author_names,
                'authors_display': ', '.join(author_names),
                'category': (
                    book_record['category_id'][1]
                    if book_record.get('category_id')
                    else ''
                ),
                'language': book_record.get('language', ''),
                'publisher': book_record.get('publisher', ''),
                'publication_date': str(book_record.get('publication_date', '')),
                'pages': book_record.get('pages', 0),
                'total_copies': book_record.get('total_qty', 0),
                'available_copies': book_record.get('available_qty', 0),
                'availability_status': book_record.get('state', ''),
                'description': book_record.get('description', ''),
            }
            enriched_catalog.append(enriched_book)

        logger.info(
            f'Catálogo exportado: {len(enriched_catalog)} libro(s) '
            f'con {len(all_author_ids)} autor(es) único(s)'
        )

        # Mostrar muestra del catálogo exportado
        for enriched_book in enriched_catalog[:3]:
            logger.info(
                f"  • [{enriched_book['id']}] {enriched_book['title']} "
                f"— {enriched_book['authors_display']} "
                f"— {enriched_book['category']}"
            )
        if len(enriched_catalog) > 3:
            logger.info(f'  ... y {len(enriched_catalog) - 3} libro(s) más')

        return enriched_catalog

    # ── Caso de uso 5: Préstamos vencidos con detalle de multas ───────────────

    def get_overdue_loans_with_fees(
        self,
        minimum_overdue_days: int = 1,
        include_fee_paid: bool = False,
    ) -> Dict:
        """
        Obtiene todos los préstamos vencidos con cálculo de multas acumuladas.
        Útil para reportes de morosidad y notificaciones automatizadas.

        Args:
            minimum_overdue_days: Días mínimos de retraso para incluir.
            include_fee_paid:     Si True, incluye también los que ya pagaron.

        Returns:
            Dict con 'overdue_loans', 'total_fees_pending',
            'affected_members_count' y 'most_overdue'.
        """
        logger.info('=== CASO 5: Préstamos vencidos con detalle de multas ===')

        overdue_search_domain = [
            ('state', '=', 'loaned'),
            ('days_overdue', '>=', minimum_overdue_days),
        ]

        if not include_fee_paid:
            overdue_search_domain.append(('fee_paid', '=', False))

        overdue_loans = self.client.execute_kw(
            self.LOAN_MODEL,
            'search_read',
            [overdue_search_domain],
            {
                'fields': [
                    'reference',
                    'member_id',
                    'book_id',
                    'book_authors',
                    'loan_date',
                    'expected_return_date',
                    'days_overdue',
                    'late_fee',
                    'fee_paid',
                    'currency_id',
                ],
                'order': 'days_overdue desc',
            },
        )

        if not overdue_loans:
            logger.info(
                f'No hay préstamos vencidos con más de {minimum_overdue_days} día(s)'
            )
            return {
                'overdue_loans': [],
                'total_fees_pending': 0.0,
                'affected_members_count': 0,
                'most_overdue': None,
            }

        total_fees_pending = sum(
            loan_record['late_fee'] for loan_record in overdue_loans
        )
        affected_member_ids = {
            loan_record['member_id'][0]
            for loan_record in overdue_loans
            if loan_record.get('member_id')
        }
        most_overdue_loan = overdue_loans[0]  # Ya ordenados por days_overdue desc

        overdue_summary = {
            'overdue_loans': overdue_loans,
            'total_fees_pending': total_fees_pending,
            'affected_members_count': len(affected_member_ids),
            'most_overdue': most_overdue_loan,
        }

        logger.info(
            f'Préstamos vencidos encontrados: {len(overdue_loans)}'
        )
        logger.info(
            f'Total multas pendientes: ${total_fees_pending:.2f} | '
            f'Socios afectados: {len(affected_member_ids)}'
        )
        logger.info(
            f'Mayor retraso: {most_overdue_loan["reference"]} — '
            f'{most_overdue_loan["book_id"][1]} — '
            f'{most_overdue_loan["days_overdue"]} días — '
            f'Multa: ${most_overdue_loan["late_fee"]:.2f}'
        )

        logger.info('\nDetalle de préstamos vencidos:')
        for loan_record in overdue_loans:
            fee_status = '(PAGADO)' if loan_record['fee_paid'] else '(PENDIENTE)'
            logger.info(
                f"  [{loan_record['reference']}] "
                f"{loan_record['member_id'][1]} — "
                f"{loan_record['book_id'][1]} — "
                f"{loan_record['days_overdue']} días — "
                f"${loan_record['late_fee']:.2f} {fee_status}"
            )

        return overdue_summary

    # ── Caso de uso 6: Uso del Context ───────────────────────────────────────

    def demo_context_usage(self) -> Dict:
        """
        Demuestra los tres principales casos de uso del Context en RPC.

        El Context es un diccionario que se pasa en kwargs de execute_kw y
        modifica el comportamiento del ORM de forma dinámica, sin cambiar
        la lógica del modelo.

        Casos demostrados:
        - allowed_company_ids : Forzar consulta a una empresa específica
        - lang                : Recibir valores de campos traducibles en el
                                idioma indicado (ej. 'es_MX')
        - active_test: False  : Incluir registros archivados en la búsqueda

        Returns:
            Diccionario con los resultados de los tres sub-casos.
        """
        logger.info('=== CASO 6: Uso del Context en JSON-RPC ===')

        # ── Sub-caso 6a: Multi-empresa ────────────────────────────────────────
        # allowed_company_ids restringe el entorno a las empresas indicadas.
        # Útil en instancias multi-empresa para aislar datos por compañía.
        logger.info('--- 6a: Context multi-empresa (allowed_company_ids) ---')
        books_filtered_by_company = self.client.execute_kw(
            self.BOOK_MODEL,
            'search_read',
            [[]],
            {
                'fields': ['name', 'state', 'available_qty'],
                'limit': 3,
                'context': {
                    'allowed_company_ids': [1],  # ID de la empresa principal
                },
            },
        )
        logger.info(
            f'Libros visibles en empresa 1: {len(books_filtered_by_company)}'
        )
        for book_record in books_filtered_by_company:
            logger.info(f"  [{book_record['state']}] {book_record['name']}")

        # ── Sub-caso 6b: Idioma / Traducciones ───────────────────────────────
        # La clave 'lang' fuerza el idioma de los campos traducibles (Char,
        # Text, Html con translate=True). Sin este context, Odoo devuelve
        # el valor en el idioma de la sesión del usuario autenticado.
        logger.info('--- 6b: Context de idioma (lang) ---')
        books_in_spanish = self.client.execute_kw(
            self.BOOK_MODEL,
            'search_read',
            [[]],
            {
                'fields': ['name', 'state'],
                'limit': 3,
                'context': {
                    'lang': 'es_MX',
                },
            },
        )
        logger.info(
            f'Libros con lang=es_MX: {len(books_in_spanish)} registro(s)'
        )
        for book_record in books_in_spanish:
            logger.info(f"  {book_record['name']} ({book_record['state']})")

        # ── Sub-caso 6c: Registros archivados (active_test: False) ───────────
        # Por defecto el ORM filtra automáticamente los registros con
        # active=False. Pasando active_test: False en el context se desactiva
        # ese filtro, permitiendo incluirlos en la búsqueda o dominio.
        logger.info('--- 6c: Context para registros archivados (active_test) ---')
        all_books_including_archived = self.client.execute_kw(
            self.BOOK_MODEL,
            'search_read',
            [[('active', 'in', [True, False])]],
            {
                'fields': ['name', 'active', 'state'],
                'limit': 5,
                'context': {
                    'active_test': False,
                },
            },
        )
        archived_books = [
            book_record for book_record in all_books_including_archived
            if not book_record['active']
        ]
        active_books = [
            book_record for book_record in all_books_including_archived
            if book_record['active']
        ]
        logger.info(
            f'Resultado con active_test=False: '
            f'{len(active_books)} activo(s), {len(archived_books)} archivado(s)'
        )
        for book_record in archived_books:
            logger.info(f"  [ARCHIVADO] {book_record['name']}")

        context_demo_results = {
            'multi_company': books_filtered_by_company,
            'translated_es_mx': books_in_spanish,
            'including_archived': all_books_including_archived,
        }

        logger.info('Context demo completado.')
        return context_demo_results


# ── Funciones de demostración de cada caso de uso ────────────────────────────

def demo_library_dashboard(library_manager: LibraryJSONRPCManager) -> Dict:
    """Demuestra el dashboard estadístico de la biblioteca."""
    return library_manager.get_library_dashboard()


def demo_member_registration(library_manager: LibraryJSONRPCManager) -> Optional[int]:
    """Demuestra el registro de un nuevo socio."""
    return library_manager.register_new_member(
        full_name='Ana González Pérez',
        email_address='ana.gonzalez@ejemplo.com',
        phone_number='+52 55 1234 5678',
        membership_type='regular',
        street_address='Av. Reforma 100, Ciudad de México',
    )


def demo_advanced_book_search(library_manager: LibraryJSONRPCManager) -> Dict:
    """Demuestra la búsqueda avanzada con paginación."""
    return library_manager.search_books_with_pagination(
        search_filters={'language': 'es', 'state': ['available', 'low_stock']},
        page_number=1,
        page_size=5,
        sort_field='name',
        sort_direction='asc',
    )


def demo_catalog_export(library_manager: LibraryJSONRPCManager) -> List[Dict]:
    """Demuestra la exportación del catálogo completo."""
    return library_manager.export_full_catalog(include_unavailable=False)


def demo_overdue_loans(library_manager: LibraryJSONRPCManager) -> Dict:
    """Demuestra la consulta de préstamos vencidos con multas."""
    return library_manager.get_overdue_loans_with_fees(
        minimum_overdue_days=1,
        include_fee_paid=False,
    )


def demo_context_usage(library_manager: LibraryJSONRPCManager) -> Dict:
    """
    Demuestra el uso del Context en llamadas JSON-RPC.

    Cubre los tres casos del slide 'El Uso del Entorno Context en RPC':
    - Multi-empresa : allowed_company_ids
    - Idioma        : lang
    - Archivados    : active_test: False
    """
    return library_manager.demo_context_usage()


# ── Punto de entrada principal ────────────────────────────────────────────────

def main():
    """
    Función principal que ejecuta todos los casos de uso de demostración.
    Ajusta las constantes de conexión según tu entorno.
    """
    # ── Configuración de conexión ─────────────────────────────────────────────
    SERVER_URL = 'http://localhost:8069'
    DATABASE_NAME = 'OdootrainingNleon'
    USERNAME = 'admin'
    API_KEY = 'c6a6b37270ccdb503c794b572d5890d7cec94bcb'  # Generar en Preferencias → Seguridad de cuenta → Claves API

    logger.info('=' * 60)
    logger.info('  Demo JSON-RPC — solt_library')
    logger.info('=' * 60)

    odoo_client = OdooJSONRPCClient(
        SERVER_URL, DATABASE_NAME, USERNAME, API_KEY,
        request_timeout_seconds=30,
        max_retry_attempts=3,
    )

    if not odoo_client.authenticate():
        logger.error('No se pudo autenticar. Verifica las credenciales.')
        return

    library_manager = LibraryJSONRPCManager(odoo_client)

    # Caso 1: Dashboard estadístico
    library_dashboard = demo_library_dashboard(library_manager)
    logger.info(
        f"Dashboard generado a las {library_dashboard.get('generated_at')}\n"
    )

    # Caso 2: Registro de nuevo socio (descomenta para ejecutar)
    # new_member_id = demo_member_registration(library_manager)
    # logger.info(f'Nuevo miembro registrado con ID: {new_member_id}\n')

    # Caso 3: Búsqueda avanzada con paginación
    search_results = demo_advanced_book_search(library_manager)
    logger.info(
        f"Búsqueda retornó página 1 de {search_results.get('total_pages', 0)} "
        f"({search_results.get('total_books', 0)} libros en total)\n"
    )

    # Caso 4: Exportación del catálogo
    catalog_export = demo_catalog_export(library_manager)
    logger.info(f'Catálogo exportado: {len(catalog_export)} libro(s)\n')

    # Caso 5: Préstamos vencidos con multas
    overdue_report = demo_overdue_loans(library_manager)
    logger.info(
        f"Préstamos vencidos: {len(overdue_report.get('overdue_loans', []))} | "
        f"Total multas: ${overdue_report.get('total_fees_pending', 0.0):.2f}\n"
    )

    # Caso 6: Uso del Context (multi-empresa, idioma, registros archivados)
    context_results = demo_context_usage(library_manager)
    logger.info(
        f"Context demo: "
        f"{len(context_results.get('multi_company', []))} libro(s) empresa 1 | "
        f"{len(context_results.get('translated_es_mx', []))} libro(s) es_MX | "
        f"{len(context_results.get('including_archived', []))} registro(s) con archivados\n"
    )

    logger.info('=' * 60)
    logger.info('  Demo JSON-RPC completada')
    logger.info('=' * 60)


if __name__ == '__main__':
    main()
