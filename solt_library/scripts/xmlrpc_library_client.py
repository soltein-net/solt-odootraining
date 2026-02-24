#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente XML-RPC para solt_library
===================================

Este script demuestra cómo interactuar con el módulo solt_library usando XML-RPC.
Basado en la documentación oficial de Odoo 17 y buenas prácticas de desarrollo.

Casos de uso implementados:
1. Consulta de catálogo de libros disponibles (con filtros por categoría y estado)
2. Registro y confirmación de un nuevo préstamo
3. Devolución de un libro prestado
4. Historial de préstamos de un miembro específico
5. Búsqueda de libros por autor

Modelos utilizados:
- library.book   : Catálogo de libros
- library.loan   : Préstamos activos e históricos
- library.member : Socios registrados de la biblioteca
- library.author : Autores del catálogo

Autor: Soltein Training
Fecha: 2026
"""

import logging
import sys
import xmlrpc.client
from datetime import datetime
from typing import Any, Dict, List, Optional

# ── Configuración de logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('xmlrpc_library.log'),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ── Cliente XML-RPC base ──────────────────────────────────────────────────────

class OdooXMLRPCClient:
    """
    Cliente XML-RPC genérico para Odoo 17.
    Gestiona la autenticación y la ejecución de métodos remotos.
    """

    def __init__(
        self,
        server_url: str,
        database_name: str,
        username: str,
        api_key: str,
    ):
        self.server_url = server_url
        self.database_name = database_name
        self.username = username
        self.api_key = api_key
        self.authenticated_user_id: Optional[int] = None

        self.common_proxy = xmlrpc.client.ServerProxy(
            f'{server_url}/xmlrpc/2/common'
        )
        self.object_proxy = xmlrpc.client.ServerProxy(
            f'{server_url}/xmlrpc/2/object'
        )

        logger.info(f'Cliente XML-RPC inicializado para {server_url}')

    def authenticate(self) -> bool:
        """
        Autentica al usuario contra Odoo y almacena el user_id.

        Returns:
            bool: True si la autenticación fue exitosa.
        """
        try:
            server_version_info = self.common_proxy.version()
            logger.info(
                f"Conectado a Odoo {server_version_info.get('server_version', 'desconocida')}"
            )

            self.authenticated_user_id = self.common_proxy.authenticate(
                self.database_name,
                self.username,
                self.api_key,
                {},
            )

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
        Ejecuta un método en un modelo de Odoo vía XML-RPC.

        Args:
            model_name:      Nombre técnico del modelo (ej. 'library.book').
            method_name:     Método ORM a invocar (ej. 'search_read').
            positional_args: Lista de argumentos posicionales.
            keyword_args:    Diccionario de argumentos con nombre.

        Returns:
            El resultado devuelto por Odoo.

        Raises:
            RuntimeError: Si el usuario no está autenticado.
        """
        if not self.authenticated_user_id:
            raise RuntimeError(
                'Usuario no autenticado. Llama a authenticate() primero.'
            )

        positional_args = positional_args or []
        keyword_args = keyword_args or {}

        try:
            return self.object_proxy.execute_kw(
                self.database_name,
                self.authenticated_user_id,
                self.api_key,
                model_name,
                method_name,
                positional_args,
                keyword_args,
            )
        except Exception as execution_error:
            logger.error(
                f'Error ejecutando {model_name}.{method_name}: {execution_error}'
            )
            raise


# ── Gestor especializado para solt_library ────────────────────────────────────

class LibraryXMLRPCManager:
    """
    Gestor de operaciones de la biblioteca vía XML-RPC.
    Encapsula las operaciones sobre library.book, library.loan,
    library.member y library.author.
    """

    BOOK_MODEL = 'library.book'
    LOAN_MODEL = 'library.loan'
    MEMBER_MODEL = 'library.member'
    AUTHOR_MODEL = 'library.author'

    def __init__(self, client: OdooXMLRPCClient):
        self.client = client

    # ── Caso de uso 1: Catálogo de libros disponibles ─────────────────────────

    def get_available_books(
        self,
        category_id: Optional[int] = None,
        language_code: Optional[str] = None,
        result_limit: int = 20,
    ) -> List[Dict]:
        """
        Retorna los libros disponibles para préstamo, con filtros opcionales.

        Args:
            category_id:  ID de la categoría para filtrar (None = todas).
            language_code: Código de idioma, ej. 'es', 'en' (None = todos).
            result_limit: Número máximo de libros a retornar.

        Returns:
            Lista de diccionarios con la información de cada libro disponible.
        """
        logger.info('=== CASO 1: Consulta de catálogo disponible ===')

        search_domain = [('state', '=', 'available'), ('available_qty', '>', 0)]

        if category_id:
            search_domain.append(('category_id', '=', category_id))

        if language_code:
            search_domain.append(('language', '=', language_code))

        logger.info(f'Dominio de búsqueda: {search_domain}')

        available_books = self.client.execute_kw(
            self.BOOK_MODEL,
            'search_read',
            [search_domain],
            {
                'fields': [
                    'id',
                    'name',
                    'isbn',
                    'author_ids',
                    'category_id',
                    'language',
                    'available_qty',
                    'total_qty',
                    'publisher',
                    'publication_date',
                    'state',
                ],
                'limit': result_limit,
                'order': 'name asc',
            },
        )

        logger.info(f'Libros disponibles encontrados: {len(available_books)}')
        for book in available_books:
            logger.info(
                f"  • [{book['id']}] {book['name']} "
                f"— Disponibles: {book['available_qty']}/{book['total_qty']}"
            )

        return available_books

    # ── Caso de uso 2: Registro y confirmación de préstamo ────────────────────

    def register_and_confirm_loan(
        self,
        member_id: int,
        book_id: int,
        loan_notes: str = '',
    ) -> Optional[int]:
        """
        Crea un préstamo en estado borrador y lo confirma en un solo flujo.

        Args:
            member_id:  ID del socio que solicita el préstamo.
            book_id:    ID del libro a prestar.
            loan_notes: Notas opcionales del bibliotecario.

        Returns:
            ID del préstamo creado y confirmado, o None si falla.
        """
        logger.info('=== CASO 2: Registro y confirmación de préstamo ===')

        # Verificar disponibilidad antes de crear
        book_availability_list = self.client.execute_kw(
            self.BOOK_MODEL,
            'read',
            [[book_id]],
            {'fields': ['name', 'available_qty', 'state']},
        )

        if not book_availability_list:
            logger.error(f'Libro {book_id} no encontrado')
            return None

        book_availability = book_availability_list[0]
        if book_availability['available_qty'] <= 0:
            logger.error(
                f"Sin copias disponibles de '{book_availability['name']}'"
            )
            return None

        # Crear el préstamo en estado borrador
        new_loan_id = self.client.execute_kw(
            self.LOAN_MODEL,
            'create',
            [{
                'member_id': member_id,
                'book_id': book_id,
                'loan_date': datetime.today().strftime('%Y-%m-%d'),
                'notes': loan_notes,
            }],
        )

        logger.info(f'Préstamo borrador creado con ID: {new_loan_id}')

        # Confirmar el préstamo (cambia estado a 'loaned')
        self.client.execute_kw(
            self.LOAN_MODEL,
            'action_confirm',
            [[new_loan_id]],
        )

        logger.info(
            f"Préstamo {new_loan_id} confirmado: "
            f"'{book_availability['name']}' → miembro {member_id}"
        )

        return new_loan_id

    # ── Caso de uso 3: Devolución de libro ────────────────────────────────────

    def return_book(self, loan_id: int) -> bool:
        """
        Registra la devolución de un libro prestado.

        Args:
            loan_id: ID del préstamo activo a cerrar.

        Returns:
            True si la devolución fue exitosa.
        """
        logger.info('=== CASO 3: Devolución de libro ===')

        # Leer información del préstamo antes de devolver
        loan_detail_list = self.client.execute_kw(
            self.LOAN_MODEL,
            'read',
            [[loan_id]],
            {
                'fields': [
                    'reference',
                    'book_id',
                    'member_id',
                    'state',
                    'days_overdue',
                    'late_fee',
                ],
            },
        )

        if not loan_detail_list:
            logger.error(f'Préstamo {loan_id} no encontrado')
            return False

        loan_detail = loan_detail_list[0]

        if loan_detail['state'] != 'loaned':
            logger.error(
                f"El préstamo {loan_id} está en estado '{loan_detail['state']}', "
                f"solo se pueden devolver préstamos activos"
            )
            return False

        # Ejecutar devolución
        self.client.execute_kw(
            self.LOAN_MODEL,
            'action_return',
            [[loan_id]],
        )

        logger.info(
            f"Devolución registrada — Referencia: {loan_detail['reference']}, "
            f"Libro: {loan_detail['book_id'][1]}, "
            f"Miembro: {loan_detail['member_id'][1]}"
        )

        if loan_detail['days_overdue'] > 0:
            logger.warning(
                f"  Devolución tardía: {loan_detail['days_overdue']} días — "
                f"Multa: ${loan_detail['late_fee']:.2f}"
            )

        return True

    # ── Caso de uso 4: Historial de préstamos de un miembro ───────────────────

    def get_member_loan_history(
        self,
        member_id: int,
        loan_state_filter: Optional[str] = None,
        history_limit: int = 50,
    ) -> List[Dict]:
        """
        Retorna el historial de préstamos de un socio específico.

        Args:
            member_id:          ID del miembro de la biblioteca.
            loan_state_filter:  Filtrar por estado ('loaned', 'returned', 'lost').
                                None retorna todos los estados.
            history_limit:      Número máximo de registros.

        Returns:
            Lista de préstamos del miembro ordenados por fecha descendente.
        """
        logger.info('=== CASO 4: Historial de préstamos de miembro ===')

        # Datos del miembro
        member_data_list = self.client.execute_kw(
            self.MEMBER_MODEL,
            'read',
            [[member_id]],
            {
                'fields': [
                    'name',
                    'code',
                    'membership_type',
                    'active_loan_count',
                    'overdue_loan_count',
                    'pending_fees',
                    'state',
                ],
            },
        )

        if not member_data_list:
            logger.error(f'Miembro {member_id} no encontrado')
            return []

        member_data = member_data_list[0]
        logger.info(
            f"Miembro: {member_data['name']} ({member_data['code']}) "
            f"— Tipo: {member_data['membership_type']} "
            f"— Estado: {member_data['state']}"
        )
        logger.info(
            f"  Préstamos activos: {member_data['active_loan_count']} | "
            f"Vencidos: {member_data['overdue_loan_count']} | "
            f"Multas pendientes: ${member_data['pending_fees']:.2f}"
        )

        # Construir dominio de búsqueda de préstamos
        loan_search_domain = [('member_id', '=', member_id)]
        if loan_state_filter:
            loan_search_domain.append(('state', '=', loan_state_filter))

        loan_history = self.client.execute_kw(
            self.LOAN_MODEL,
            'search_read',
            [loan_search_domain],
            {
                'fields': [
                    'reference',
                    'book_id',
                    'book_authors',
                    'loan_date',
                    'expected_return_date',
                    'actual_return_date',
                    'state',
                    'days_overdue',
                    'late_fee',
                    'fee_paid',
                ],
                'limit': history_limit,
                'order': 'loan_date desc',
            },
        )

        logger.info(
            f'Préstamos encontrados para {member_data["name"]}: {len(loan_history)}'
        )
        for loan_record in loan_history:
            logger.info(
                f"  [{loan_record['reference']}] {loan_record['book_id'][1]} "
                f"— Estado: {loan_record['state']} "
                f"— Préstamo: {loan_record['loan_date']}"
            )

        return loan_history

    # ── Caso de uso 5: Búsqueda de libros por autor ───────────────────────────

    def search_books_by_author(
        self,
        author_name_query: str,
        availability_only: bool = False,
    ) -> List[Dict]:
        """
        Busca libros cuyo autor coincida con el término de búsqueda.

        Args:
            author_name_query: Término de búsqueda parcial del nombre del autor.
            availability_only: Si True, retorna solo libros disponibles.

        Returns:
            Lista de libros del autor encontrado, con sus datos principales.
        """
        logger.info('=== CASO 5: Búsqueda de libros por autor ===')
        logger.info(f'Buscando autores con nombre que contenga: "{author_name_query}"')

        # Buscar autores que coincidan
        matching_authors = self.client.execute_kw(
            self.AUTHOR_MODEL,
            'search_read',
            [[('name', 'ilike', author_name_query)]],
            {
                'fields': ['id', 'name', 'nationality', 'book_count'],
                'limit': 10,
            },
        )

        if not matching_authors:
            logger.warning(f'No se encontraron autores con: "{author_name_query}"')
            return []

        for author_record in matching_authors:
            logger.info(
                f"  Autor encontrado: {author_record['name']} "
                f"({author_record['nationality']}) — "
                f"{author_record['book_count']} libro(s) en catálogo"
            )

        matched_author_ids = [author_record['id'] for author_record in matching_authors]

        # Buscar libros de esos autores
        book_search_domain = [('author_ids', 'in', matched_author_ids)]
        if availability_only:
            book_search_domain.append(('state', '=', 'available'))

        books_by_author = self.client.execute_kw(
            self.BOOK_MODEL,
            'search_read',
            [book_search_domain],
            {
                'fields': [
                    'id',
                    'name',
                    'isbn',
                    'author_ids',
                    'category_id',
                    'available_qty',
                    'total_qty',
                    'state',
                    'language',
                    'publication_date',
                ],
                'order': 'name asc',
            },
        )

        logger.info(
            f'Libros encontrados para autores "{author_name_query}": '
            f'{len(books_by_author)}'
        )
        for book_record in books_by_author:
            availability_status = (
                f'Disponibles: {book_record["available_qty"]}/{book_record["total_qty"]}'
            )
            logger.info(
                f"  • [{book_record['id']}] {book_record['name']} "
                f"— {availability_status} — Estado: {book_record['state']}"
            )

        return books_by_author


# ── Funciones de demostración de cada caso de uso ────────────────────────────

def demo_available_books_catalog(library_manager: LibraryXMLRPCManager) -> List[Dict]:
    """Demuestra la consulta del catálogo de libros disponibles."""
    available_books = library_manager.get_available_books(
        language_code='es',
        result_limit=10,
    )
    return available_books


def demo_loan_registration(
    library_manager: LibraryXMLRPCManager,
    member_id: int,
    book_id: int,
) -> Optional[int]:
    """Demuestra el registro y confirmación de un nuevo préstamo."""
    new_loan_id = library_manager.register_and_confirm_loan(
        member_id=member_id,
        book_id=book_id,
        loan_notes='Préstamo registrado vía XML-RPC — demo de integración',
    )
    return new_loan_id


def demo_book_return(
    library_manager: LibraryXMLRPCManager,
    loan_id: int,
) -> bool:
    """Demuestra la devolución de un libro prestado."""
    return_success = library_manager.return_book(loan_id=loan_id)
    return return_success


def demo_member_history(
    library_manager: LibraryXMLRPCManager,
    member_id: int,
) -> List[Dict]:
    """Demuestra la consulta del historial completo de un socio."""
    loan_history = library_manager.get_member_loan_history(
        member_id=member_id,
        history_limit=20,
    )
    return loan_history


def demo_search_by_author(
    library_manager: LibraryXMLRPCManager,
    author_name_query: str,
) -> List[Dict]:
    """Demuestra la búsqueda de libros por nombre de autor."""
    author_books = library_manager.search_books_by_author(
        author_name_query=author_name_query,
        availability_only=False,
    )
    return author_books


# ── Punto de entrada principal ────────────────────────────────────────────────

def main():
    """
    Función principal que ejecuta todos los casos de uso de demostración.
    Ajusta las constantes de conexión y los IDs de prueba según tu entorno.
    """
    # ── Configuración de conexión ─────────────────────────────────────────────
    SERVER_URL = 'http://localhost:8069'
    DATABASE_NAME = 'OdootrainingNleon'
    USERNAME = 'admin'
    API_KEY = 'c6a6b37270ccdb503c794b572d5890d7cec94bcb'  # Generar en Preferencias → Seguridad de cuenta → Claves API


    # ── IDs de prueba (ajustar según datos de tu base de datos) ──────────────
    TEST_MEMBER_ID = 1    # ID de un socio activo
    TEST_BOOK_ID = 1      # ID de un libro disponible
    TEST_LOAN_ID = 1      # ID de un préstamo activo para devolución
    TEST_AUTHOR_QUERY = 'García'  # Fragmento del nombre del autor a buscar

    logger.info('=' * 60)
    logger.info('  Demo XML-RPC — solt_library')
    logger.info('=' * 60)

    # Inicializar y autenticar cliente
    odoo_client = OdooXMLRPCClient(SERVER_URL, DATABASE_NAME, USERNAME, API_KEY)

    if not odoo_client.authenticate():
        logger.error('No se pudo autenticar. Verifica las credenciales.')
        return

    # Crear gestor de biblioteca
    library_manager = LibraryXMLRPCManager(odoo_client)

    # Caso 1: Catálogo de libros disponibles
    #available_books = demo_available_books_catalog(library_manager)
    #logger.info(f'Catálogo retornó {len(available_books)} libro(s)\n')

    # Caso 2: Registrar un préstamo (descomenta para ejecutar)
    #new_loan_id = demo_loan_registration(library_manager, TEST_MEMBER_ID, TEST_BOOK_ID)
    #logger.info(f'Préstamo registrado: {new_loan_id}')

    # Caso 3: Devolver un libro (descomenta para ejecutar)
    demo_book_return(library_manager, TEST_LOAN_ID)

    # Caso 4: Historial de miembro
    #loan_history = demo_member_history(library_manager, TEST_MEMBER_ID)
    #logger.info(f'Historial retornó {len(loan_history)} préstamo(s)\n')

    # Caso 5: Búsqueda por autor
    author_books = demo_search_by_author(library_manager, TEST_AUTHOR_QUERY)
    logger.info(f'Búsqueda por autor retornó {len(author_books)} libro(s)\n')

    logger.info('=' * 60)
    logger.info('  Demo XML-RPC completada')
    logger.info('=' * 60)


if __name__ == '__main__':
    main()