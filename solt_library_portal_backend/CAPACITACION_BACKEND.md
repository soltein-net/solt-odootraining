# Capacitación: Personalización del Portal en Odoo 17 - Backend

## Módulo: `solt_library_portal_backend`

---

## Índice

1. [Introducción al Portal en Odoo 17](#1-introducción-al-portal-en-odoo-17)
2. [Arquitectura del Portal](#2-arquitectura-del-portal)
3. [Controladores HTTP](#3-controladores-http)
4. [Rutas y Decoradores](#4-rutas-y-decoradores)
5. [Acceso a Datos desde el Portal](#5-acceso-a-datos-desde-el-portal)
6. [Seguridad en el Portal](#6-seguridad-en-el-portal)
7. [Extensión de Modelos para el Portal](#7-extensión-de-modelos-para-el-portal)
8. [Análisis del Código del Módulo](#8-análisis-del-código-del-módulo)
9. [Ejercicios Prácticos](#9-ejercicios-prácticos)

---

## 1. Introducción al Portal en Odoo 17

### ¿Qué es el Portal de Odoo?

El **Portal de Odoo** es una interfaz web que permite a usuarios externos (clientes, proveedores, socios) acceder a información específica del sistema sin necesidad de ser usuarios internos del backend.

```
┌─────────────────────────────────────────────────────────────────┐
│                         ODOO                                     │
│  ┌───────────────────┐          ┌───────────────────────────┐   │
│  │     BACKEND       │          │         PORTAL            │   │
│  │  (Usuarios        │          │  (Usuarios externos)      │   │
│  │   internos)       │          │                           │   │
│  │                   │          │  - Clientes               │   │
│  │  - Empleados      │          │  - Proveedores            │   │
│  │  - Administradores│   ◄────► │  - Socios                 │   │
│  │  - Gerentes       │          │  - Miembros (biblioteca)  │   │
│  │                   │          │                           │   │
│  │  Acceso completo  │          │  Acceso limitado          │   │
│  │  al ERP           │          │  a sus datos              │   │
│  └───────────────────┘          └───────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Diferencias entre Backend y Portal

| Aspecto | Backend | Portal |
|---------|---------|--------|
| **Usuarios** | Internos (empleados) | Externos (clientes, socios) |
| **Acceso** | Completo al ERP | Solo a datos propios |
| **Interfaz** | Compleja, muchas opciones | Simplificada, específica |
| **Autenticación** | Usuario/Contraseña Odoo | Portal login |
| **Grupo de seguridad** | `base.group_user` | `base.group_portal` |

### Casos de Uso Comunes

1. **E-commerce**: Clientes ven sus pedidos, facturas
2. **Proyectos**: Clientes ven tareas y progreso
3. **Helpdesk**: Usuarios ven sus tickets
4. **Biblioteca**: Miembros ven catálogo y préstamos

---

## 2. Arquitectura del Portal

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DEL PORTAL                       │
│                                                                  │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │  TEMPLATES  │◄───│ CONTROLLERS │───►│   MODELS    │        │
│   │   (QWeb)    │    │   (HTTP)    │    │   (ORM)     │        │
│   └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                  │                   │                │
│         │                  │                   │                │
│         ▼                  ▼                   ▼                │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │   ASSETS    │    │  SECURITY   │    │    DATA     │        │
│   │  (CSS/JS)   │    │  (Rules)    │    │ (Database)  │        │
│   └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de una Petición al Portal

```
1. Usuario accede a /my/library
         │
         ▼
2. Odoo busca la ruta en los controladores
         │
         ▼
3. Ejecuta el método del controlador
         │
         ▼
4. El controlador consulta datos via ORM
         │
         ▼
5. Las reglas de seguridad filtran los datos
         │
         ▼
6. El controlador prepara los valores
         │
         ▼
7. Renderiza el template QWeb con los valores
         │
         ▼
8. Retorna HTML al navegador
```

### Módulos Base del Portal

```python
depends = [
    'portal',   # Framework base del portal
    'website',  # Funcionalidades web (layout, menús)
]
```

---

## 3. Controladores HTTP

### ¿Qué es un Controlador?

Un **controlador** es una clase Python que define **rutas HTTP** y su lógica asociada. Procesa las peticiones del navegador y retorna respuestas.

### Estructura Básica

```python
from odoo import http
from odoo.http import request

class MiControlador(http.Controller):
    """
    Controlador independiente.
    Para funcionalidades que NO se integran al portal existente.
    """

    @http.route('/mi/ruta', type='http', auth='public', website=True)
    def mi_metodo(self, **kw):
        # Lógica
        return request.render('mi_modulo.mi_template', valores)
```

### Herencia de CustomerPortal

```python
from odoo.addons.portal.controllers.portal import CustomerPortal

class MiPortal(CustomerPortal):
    """
    Hereda de CustomerPortal para integrar con el portal existente.
    Esto permite agregar secciones en "Mi Cuenta".
    """

    def _prepare_home_portal_values(self, counters):
        """
        Método especial para agregar contadores en la página principal.
        """
        values = super()._prepare_home_portal_values(counters)
        # Agregar nuestros contadores
        if 'mi_contador' in counters:
            values['mi_contador'] = 10
        return values
```

### El Objeto `request`

```python
from odoo.http import request

# Acceso al entorno ORM
env = request.env

# Usuario actual
user = request.env.user

# Partner del usuario
partner = request.env.user.partner_id

# Parámetros de la URL
params = request.params

# Renderizar template
return request.render('modulo.template', valores)

# Redireccionar
return request.redirect('/otra/ruta')
```

---

## 4. Rutas y Decoradores

### Anatomía de @http.route()

```python
@http.route(
    route=['/mi/ruta', '/mi/ruta/page/<int:page>'],  # URLs (puede ser lista)
    type='http',        # 'http' para HTML, 'json' para API
    auth='user',        # 'public', 'user', 'none'
    website=True,       # Usar layout del website
    methods=['GET'],    # Métodos HTTP permitidos
    csrf=True,          # Protección CSRF (default True)
)
def mi_metodo(self, page=1, **kw):
    pass
```

### Tipos de Autenticación (auth)

| Valor | Descripción | Uso |
|-------|-------------|-----|
| `'public'` | Cualquier visitante | Páginas públicas, catálogo |
| `'user'` | Usuario autenticado | Datos personales, préstamos |
| `'none'` | Sin verificación | APIs internas, webhooks |

### Ejemplos de Rutas

```python
# Ruta simple pública
@http.route('/library/catalog', type='http', auth='public', website=True)
def catalog(self):
    pass

# Ruta con parámetro en URL
@http.route('/library/book/<int:book_id>', type='http', auth='public', website=True)
def book_detail(self, book_id):
    pass

# Ruta con paginación
@http.route(['/my/loans', '/my/loans/page/<int:page>'], type='http', auth='user', website=True)
def my_loans(self, page=1):
    pass

# Ruta JSON para AJAX
@http.route('/library/search', type='json', auth='public', methods=['POST'])
def search(self, query=''):
    return {'results': [...]}
```

### Captura de Parámetros

```python
# Parámetros en la URL (path)
@http.route('/book/<int:book_id>/author/<string:author_name>')
def example(self, book_id, author_name):
    # book_id = 5 (entero)
    # author_name = "cervantes" (string)
    pass

# Parámetros de query string (?param=value)
@http.route('/search')
def search(self, query='', category=None, **kw):
    # /search?query=python&category=5
    # query = "python"
    # category = "5" (string, necesita conversión)
    pass
```

---

## 5. Acceso a Datos desde el Portal

### Usando el ORM

```python
@http.route('/my/library', type='http', auth='public', website=True)
def portal_library(self):
    # Acceso al modelo con sudo() para permisos elevados
    Book = request.env['library.book'].sudo()

    # Búsqueda con dominio
    books = Book.search([
        ('state', '!=', 'unavailable'),
        ('active', '=', True)
    ])

    # Búsqueda optimizada (solo campos necesarios)
    books_data = Book.search_read(
        [('state', '!=', 'unavailable')],
        fields=['name', 'isbn', 'available_qty'],
        limit=20
    )

    return request.render('mi_modulo.template', {'books': books})
```

### ¿Por qué usar sudo()?

```python
# Los usuarios del portal tienen permisos muy limitados
# Sin sudo(), muchas consultas fallarían

# ❌ INCORRECTO - Puede fallar por permisos
books = request.env['library.book'].search([])

# ✅ CORRECTO - Usa permisos de admin
books = request.env['library.book'].sudo().search([])

# IMPORTANTE: Al usar sudo(), aplicar tus propios filtros de seguridad
# Las reglas de acceso (ir.rule) NO se aplican con sudo()
```

### Patrones Comunes de Acceso

```python
def portal_my_loans(self):
    partner = request.env.user.partner_id

    # 1. Buscar el miembro asociado al usuario
    member = request.env['library.member'].sudo().search([
        ('partner_id', '=', partner.id)
    ], limit=1)

    if not member:
        # Usuario no es miembro
        return request.render('modulo.no_member_template')

    # 2. Buscar préstamos del miembro (filtro de seguridad manual)
    loans = request.env['library.loan'].sudo().search([
        ('member_id', '=', member.id)  # ← Filtro de seguridad
    ])

    return request.render('modulo.loans_template', {'loans': loans})
```

### Paginación con portal_pager

```python
from odoo.addons.portal.controllers.portal import pager as portal_pager

@http.route(['/my/library', '/my/library/page/<int:page>'], ...)
def portal_library(self, page=1, **kw):
    Book = request.env['library.book'].sudo()

    # Contar total de registros
    book_count = Book.search_count([('active', '=', True)])

    # Crear paginador
    pager = portal_pager(
        url='/my/library',
        url_args={},  # Parámetros adicionales de URL
        total=book_count,
        page=page,
        step=12  # Registros por página
    )

    # Obtener registros de la página actual
    books = Book.search(
        [('active', '=', True)],
        limit=12,
        offset=pager['offset']
    )

    return request.render('modulo.template', {
        'books': books,
        'pager': pager
    })
```

---

## 6. Seguridad en el Portal

### Niveles de Seguridad

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPAS DE SEGURIDAD                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  1. AUTENTICACIÓN (auth='user')                         │    │
│  │     → Verifica que el usuario esté logueado             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  2. PERMISOS DE MODELO (ir.model.access)                │    │
│  │     → Define qué operaciones puede hacer el grupo       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  3. REGLAS DE REGISTRO (ir.rule)                        │    │
│  │     → Define QUÉ registros puede ver/editar             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  4. LÓGICA DEL CONTROLADOR                              │    │
│  │     → Validaciones adicionales en código Python         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Permisos de Modelo (ir.model.access.csv)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_book_portal,library.book.portal,model_library_book,base.group_portal,1,0,0,0
```

| Columna | Descripción |
|---------|-------------|
| `group_id:id` | Grupo al que aplica (base.group_portal) |
| `perm_read` | Puede leer (1=sí, 0=no) |
| `perm_write` | Puede modificar |
| `perm_create` | Puede crear |
| `perm_unlink` | Puede eliminar |

### Reglas de Registro (ir.rule)

```xml
<record id="library_loan_portal_rule" model="ir.rule">
    <field name="name">Portal: Solo mis préstamos</field>
    <field name="model_id" ref="model_library_loan"/>
    <!--
    DOMINIO: Solo préstamos donde el miembro es el usuario actual

    member_id.partner_id = navegación a través de relaciones
    user.partner_id.id = partner del usuario actual
    -->
    <field name="domain_force">[('member_id.partner_id', '=', user.partner_id.id)]</field>
    <field name="groups" eval="[(4, ref('base.group_portal'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="False"/>
    <field name="perm_create" eval="False"/>
    <field name="perm_unlink" eval="False"/>
</record>
```

### Validación en el Controlador

```python
@http.route('/my/loans/<int:loan_id>', type='http', auth='user', website=True)
def loan_detail(self, loan_id, **kw):
    partner = request.env.user.partner_id

    # Buscar miembro del usuario
    member = request.env['library.member'].sudo().search([
        ('partner_id', '=', partner.id)
    ], limit=1)

    if not member:
        return request.redirect('/my/loans')

    # ⚠️ CRÍTICO: Verificar que el préstamo pertenece al usuario
    loan = request.env['library.loan'].sudo().search([
        ('id', '=', loan_id),
        ('member_id', '=', member.id)  # ← Verificación de propiedad
    ], limit=1)

    if not loan:
        # El usuario intenta acceder a un préstamo que no es suyo
        return request.redirect('/my/loans')

    return request.render('modulo.loan_detail', {'loan': loan})
```

---

## 7. Extensión de Modelos para el Portal

### Agregar Campos y Métodos

```python
from odoo import api, fields, models

class LibraryBook(models.Model):
    _inherit = 'library.book'

    # Nuevo campo para el portal
    is_featured = fields.Boolean(
        string='Destacado en Portal',
        default=False
    )

    # Método auxiliar para el portal
    def get_portal_url(self):
        """Retorna la URL del libro en el portal."""
        self.ensure_one()
        return f'/my/library/book/{self.id}'

    def get_availability_class(self):
        """Retorna clase CSS según disponibilidad."""
        self.ensure_one()
        return {
            'available': 'success',
            'low_stock': 'warning',
            'unavailable': 'danger'
        }.get(self.state, 'secondary')
```

### Campos Computados para Visualización

```python
class LibraryBook(models.Model):
    _inherit = 'library.book'

    short_description = fields.Text(
        string='Descripción Corta',
        compute='_compute_short_description'
    )

    @api.depends('description')
    def _compute_short_description(self):
        """Trunca la descripción para listados."""
        for book in self:
            if book.description and len(book.description) > 150:
                book.short_description = book.description[:147] + '...'
            else:
                book.short_description = book.description or ''
```

---

## 8. Análisis del Código del Módulo

### Estructura del Módulo

```
solt_library_portal_backend/
├── __manifest__.py          # Configuración
├── __init__.py              # Imports
├── controllers/
│   ├── __init__.py
│   ├── portal.py            # Controlador principal del portal
│   └── main.py              # Controladores auxiliares y JSON
├── models/
│   ├── __init__.py
│   ├── library_book.py      # Extensión de libros
│   ├── library_member.py    # Extensión de miembros
│   └── res_partner.py       # Extensión de contactos
└── security/
    ├── ir.model.access.csv  # Permisos de modelo
    └── portal_security.xml  # Reglas de acceso
```

### Análisis: portal.py

**Archivo:** `controllers/portal.py`

| Método | Ruta | Propósito |
|--------|------|-----------|
| `_prepare_home_portal_values` | - | Agrega contadores al portal |
| `portal_my_library` | `/my/library` | Catálogo de libros |
| `portal_book_detail` | `/my/library/book/<id>` | Detalle de libro |
| `portal_my_loans` | `/my/loans` | Préstamos del usuario |
| `portal_loan_detail` | `/my/loans/<id>` | Detalle de préstamo |
| `portal_member_profile` | `/my/library/profile` | Perfil de miembro |

### Análisis: main.py

**Archivo:** `controllers/main.py`

| Método | Ruta | Tipo | Propósito |
|--------|------|------|-----------|
| `search_books` | `/library/search` | JSON | Búsqueda AJAX |
| `get_categories` | `/library/categories` | JSON | Lista de categorías |
| `check_availability` | `/library/check_availability` | JSON | Verificar stock |
| `get_member_stats` | `/library/my/stats` | JSON | Estadísticas |
| `download_loan_receipt` | `/my/loans/<id>/download` | HTTP | Descarga PDF |
| `book_image` | `/library/book/<id>/image` | HTTP | Imagen de libro |

### Análisis: portal_security.xml

```xml
<!-- Regla para libros: Solo activos -->
<field name="domain_force">[('active', '=', True)]</field>

<!-- Regla para membresías: Solo la propia -->
<field name="domain_force">[('partner_id', '=', user.partner_id.id)]</field>

<!-- Regla para préstamos: Solo los propios (navegación de relación) -->
<field name="domain_force">[('member_id.partner_id', '=', user.partner_id.id)]</field>
```

---

## 9. Ejercicios Prácticos

### Ejercicio 1: Agregar un Nuevo Contador

**Objetivo:** Agregar un contador de "Autores Favoritos" al portal.

```python
# En controllers/portal.py

def _prepare_home_portal_values(self, counters):
    values = super()._prepare_home_portal_values(counters)

    # TODO: Agregar contador de autores favoritos
    if 'favorite_author_count' in counters:
        # Implementar lógica
        pass

    return values
```

### Ejercicio 2: Nueva Ruta JSON

**Objetivo:** Crear un endpoint para obtener los libros más prestados.

```python
# En controllers/main.py

@http.route('/library/top_books', type='json', auth='public', methods=['POST'])
def get_top_books(self, limit=5, **kw):
    # TODO: Implementar
    # 1. Contar préstamos por libro
    # 2. Ordenar por cantidad
    # 3. Retornar los top N
    pass
```

### Ejercicio 3: Regla de Seguridad

**Objetivo:** Crear una regla que permita a los miembros premium ver información adicional.

```xml
<!-- En security/portal_security.xml -->

<record id="library_book_premium_rule" model="ir.rule">
    <field name="name">Premium: Ver libros exclusivos</field>
    <field name="model_id" ref="model_library_book"/>
    <!-- TODO: Implementar dominio -->
    <field name="domain_force">???</field>
    <field name="groups" eval="[(4, ref('base.group_portal'))]"/>
</record>
```

---

## Referencias

- [Documentación Oficial de Odoo - Controllers](https://www.odoo.com/documentation/17.0/developer/reference/backend/http.html)
- [Documentación Oficial - Security](https://www.odoo.com/documentation/17.0/developer/reference/backend/security.html)
- [Documentación Oficial - Portal](https://www.odoo.com/documentation/17.0/developer/howtos/website.html)

---

## Resumen de la Capacitación

1. ✅ El Portal es la interfaz para usuarios externos
2. ✅ Los Controladores definen rutas y lógica HTTP
3. ✅ `@http.route()` configura autenticación y tipo de respuesta
4. ✅ Usar `sudo()` para acceso a datos, pero aplicar filtros propios
5. ✅ La seguridad tiene múltiples capas: auth, permisos, reglas, código
6. ✅ Extender modelos para agregar funcionalidad específica del portal
