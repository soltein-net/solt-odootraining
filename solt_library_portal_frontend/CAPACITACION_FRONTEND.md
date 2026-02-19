# Capacitación: Personalización del Portal en Odoo 17 - Frontend

## Módulo: `solt_library_portal_frontend`

---

## Índice

1. [Introducción a Templates QWeb](#1-introducción-a-templates-qweb)
2. [Estructura del Portal Visual](#2-estructura-del-portal-visual)
3. [Directivas QWeb](#3-directivas-qweb)
4. [Herencia de Templates](#4-herencia-de-templates)
5. [Sistema de Assets](#5-sistema-de-assets)
6. [CSS y Estilos](#6-css-y-estilos)
7. [JavaScript en el Portal](#7-javascript-en-el-portal)
8. [Análisis del Código del Módulo](#8-análisis-del-código-del-módulo)
9. [Buenas Prácticas](#9-buenas-prácticas)
10. [Ejercicios Prácticos](#10-ejercicios-prácticos)

---

## 1. Introducción a Templates QWeb

### ¿Qué es QWeb?

**QWeb** es el motor de plantillas de Odoo. Permite generar HTML dinámicamente utilizando directivas especiales prefijadas con `t-`.

```xml
<!-- Ejemplo básico de QWeb -->
<template id="mi_template">
    <div>
        <h1 t-esc="libro.name"/>
        <p t-if="libro.description" t-esc="libro.description"/>
    </div>
</template>
```

### QWeb vs Otros Motores de Plantillas

| Motor | Sintaxis | Uso en |
|-------|----------|--------|
| **QWeb** | `t-esc`, `t-if`, `t-foreach` | Odoo |
| Jinja2 | `{{ }}`, `{% %}` | Python/Flask |
| EJS | `<%= %>`, `<% %>` | Node.js |
| Blade | `{{ }}`, `@if` | Laravel |

### Ubicación de Templates

```
mi_modulo/
├── views/
│   ├── portal_templates.xml      # Templates del portal
│   ├── portal_book_templates.xml # Templates de libros
│   └── ...
```

En `__manifest__.py`:
```python
'data': [
    'views/portal_templates.xml',
    'views/portal_book_templates.xml',
]
```

---

## 2. Estructura del Portal Visual

### Layout Base del Portal

```
┌─────────────────────────────────────────────────────────────────┐
│                         HEADER                                   │
│  [Logo]    [Menú]                          [Usuario] [Carrito]  │
├─────────────────────────────────────────────────────────────────┤
│                       BREADCRUMBS                                │
│  Inicio > Biblioteca > Mi Libro                                  │
├───────────────────────┬─────────────────────────────────────────┤
│                       │                                          │
│      SIDEBAR          │           CONTENIDO PRINCIPAL            │
│                       │                                          │
│  ┌─────────────────┐  │   ┌─────────────────────────────────┐   │
│  │  Mis Detalles   │  │   │                                 │   │
│  │  ─────────────  │  │   │    <o_portal_content>           │   │
│  │  Nombre         │  │   │                                 │   │
│  │  Email          │  │   │    Aquí va tu contenido         │   │
│  │                 │  │   │                                 │   │
│  └─────────────────┘  │   └─────────────────────────────────┘   │
│                       │                                          │
│  ┌─────────────────┐  │                                          │
│  │   Biblioteca    │  │                                          │
│  │  ─────────────  │  │                                          │
│  │  Catálogo       │  │                                          │
│  │  Mis Préstamos  │  │                                          │
│  │  Mi Perfil      │  │                                          │
│  └─────────────────┘  │                                          │
│                       │                                          │
├───────────────────────┴─────────────────────────────────────────┤
│                         FOOTER                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Templates Clave del Portal

| Template | Descripción |
|----------|-------------|
| `portal.portal_layout` | Layout base con header/footer |
| `portal.portal_my_home` | Página "Mi Cuenta" |
| `portal.portal_breadcrumbs` | Migas de pan |
| `portal.portal_docs_entry` | Entrada de documento |

### Usando el Layout

```xml
<template id="mi_pagina" name="Mi Página">
    <!-- Heredar del layout base -->
    <t t-call="portal.portal_layout">

        <!-- Tu contenido va aquí -->
        <div class="o_portal_content">
            <h2>Mi Página Personalizada</h2>
            <!-- ... -->
        </div>

    </t>
</template>
```

---

## 3. Directivas QWeb

### Directivas de Salida

| Directiva | Uso | Ejemplo |
|-----------|-----|---------|
| `t-esc` | Escapar y mostrar | `<span t-esc="libro.name"/>` |
| `t-raw` | Sin escapar (HTML) | `<div t-raw="libro.description"/>` |
| `t-field` | Con formato y widgets | `<span t-field="libro.price"/>` |

```xml
<!-- t-esc: Seguro, escapa HTML -->
<span t-esc="nombre"/>
<!-- Si nombre = "<script>alert('xss')</script>" -->
<!-- Muestra: &lt;script&gt;alert('xss')&lt;/script&gt; -->

<!-- t-raw: PELIGROSO, no escapar -->
<!-- Solo usar con contenido confiable -->
<div t-raw="descripcion_html"/>

<!-- t-field: Con widget automático -->
<span t-field="libro.publication_date"/>
<!-- Formatea la fecha según configuración regional -->
```

### Directivas Condicionales

```xml
<!-- t-if: Condición simple -->
<div t-if="libro.available_qty > 0">
    Disponible
</div>

<!-- t-elif y t-else -->
<t t-if="estado == 'available'">
    <span class="badge bg-success">Disponible</span>
</t>
<t t-elif="estado == 'low_stock'">
    <span class="badge bg-warning">Pocas copias</span>
</t>
<t t-else="">
    <span class="badge bg-danger">No disponible</span>
</t>

<!-- Elemento <t> es invisible en el HTML final -->
```

### Directivas de Iteración

```xml
<!-- t-foreach: Iterar sobre colección -->
<ul>
    <t t-foreach="libros" t-as="libro">
        <li>
            <t t-esc="libro.name"/>

            <!-- Variables especiales disponibles -->
            <!-- libro_index: índice (0, 1, 2...) -->
            <!-- libro_first: ¿Es el primero? -->
            <!-- libro_last: ¿Es el último? -->
            <!-- libro_odd: ¿Índice impar? -->
            <!-- libro_even: ¿Índice par? -->

            <t t-if="not libro_last">, </t>
        </li>
    </t>
</ul>

<!-- Iterar sobre diccionario -->
<t t-foreach="opciones.items()" t-as="item">
    <option t-att-value="item[0]" t-esc="item[1]['label']"/>
</t>
```

### Directivas de Atributos

```xml
<!-- t-att-*: Atributo dinámico -->
<a t-att-href="'/libro/' + str(libro.id)">Ver</a>
<!-- Resultado: <a href="/libro/5">Ver</a> -->

<span t-att-class="libro.state">Estado</span>
<!-- Resultado: <span class="available">Estado</span> -->

<!-- t-attf-*: Atributo con formato (interpolación) -->
<a t-attf-href="/libro/#{libro.id}/editar">Editar</a>
<!-- Resultado: <a href="/libro/5/editar">Editar</a> -->

<div t-attf-class="badge bg-#{libro.get_availability_class()}">
    <!-- Resultado: <div class="badge bg-success"> -->
</div>

<!-- Múltiples clases condicionales -->
<tr t-attf-class="#{libro.state == 'unavailable' and 'text-danger' or ''} #{libro_odd and 'bg-light' or ''}">
```

### Directivas de Variables

```xml
<!-- t-set/t-value: Definir variable -->
<t t-set="total" t-value="0"/>

<!-- Actualizar variable -->
<t t-foreach="items" t-as="item">
    <t t-set="total" t-value="total + item.precio"/>
</t>

<p>Total: <t t-esc="total"/></p>

<!-- Variable con contenido HTML -->
<t t-set="mensaje">
    <strong>Advertencia:</strong> Texto importante
</t>
<div t-raw="mensaje"/>
```

### Directiva t-call

```xml
<!-- Definir template reutilizable -->
<template id="tarjeta_libro">
    <div class="card">
        <h3 t-esc="libro.name"/>
        <p t-esc="libro.isbn"/>
    </div>
</template>

<!-- Llamar al template -->
<t t-foreach="libros" t-as="libro">
    <t t-call="mi_modulo.tarjeta_libro"/>
    <!-- 'libro' está disponible dentro del template llamado -->
</t>

<!-- Pasar variables adicionales -->
<t t-call="mi_modulo.tarjeta_libro">
    <t t-set="mostrar_precio" t-value="True"/>
</t>
```

---

## 4. Herencia de Templates

### Tipos de Herencia

```xml
<!-- 1. EXTENSIÓN: Agregar contenido -->
<template id="mi_extension" inherit_id="portal.portal_my_home">
    <xpath expr="//div[@class='o_portal_docs']" position="inside">
        <!-- Nuevo contenido -->
    </xpath>
</template>

<!-- 2. REEMPLAZO: Sustituir elemento -->
<template id="mi_reemplazo" inherit_id="otro_modulo.template">
    <xpath expr="//h1" position="replace">
        <h1>Nuevo Título</h1>
    </xpath>
</template>
```

### Posiciones de XPath

| Posición | Descripción |
|----------|-------------|
| `inside` | Dentro del elemento (al final) |
| `before` | Antes del elemento |
| `after` | Después del elemento |
| `replace` | Reemplaza el elemento |
| `attributes` | Modifica atributos |

```xml
<!-- inside: Agregar al final del contenido -->
<xpath expr="//div[@id='contenedor']" position="inside">
    <p>Nuevo párrafo</p>
</xpath>

<!-- before: Agregar antes -->
<xpath expr="//button[@id='enviar']" position="before">
    <button>Cancelar</button>
</xpath>

<!-- after: Agregar después -->
<xpath expr="//h1" position="after">
    <p class="lead">Subtítulo</p>
</xpath>

<!-- replace: Reemplazar completamente -->
<xpath expr="//span[@class='viejo']" position="replace">
    <span class="nuevo">Contenido nuevo</span>
</xpath>

<!-- attributes: Modificar atributos -->
<xpath expr="//div[@id='contenedor']" position="attributes">
    <attribute name="class" add="nueva-clase"/>
    <attribute name="data-valor">123</attribute>
</xpath>
```

### Selectores XPath Comunes

```xml
<!-- Por ID -->
<xpath expr="//div[@id='mi_div']" position="..."/>

<!-- Por clase -->
<xpath expr="//div[hasclass('mi-clase')]" position="..."/>

<!-- Por clase múltiple -->
<xpath expr="//div[hasclass('clase1')][hasclass('clase2')]" position="..."/>

<!-- Por atributo -->
<xpath expr="//input[@name='email']" position="..."/>

<!-- Por contenido -->
<xpath expr="//span[text()='Texto']" position="..."/>

<!-- Primer/último elemento -->
<xpath expr="(//li)[1]" position="..."/>
<xpath expr="(//li)[last()]" position="..."/>

<!-- Elemento hijo -->
<xpath expr="//ul[@id='lista']/li[2]" position="..."/>
```

### Ejemplo de Herencia en el Portal

```xml
<!-- Agregar sección de biblioteca en "Mi Cuenta" -->
<template id="portal_my_home_library"
          inherit_id="portal.portal_my_home"
          priority="40">

    <xpath expr="//div[hasclass('o_portal_docs')]" position="inside">

        <!-- Usar componente del portal -->
        <t t-call="portal.portal_docs_entry">
            <t t-set="icon" t-value="'fa fa-book'"/>
            <t t-set="title">Biblioteca</t>
            <t t-set="text">Explora el catálogo</t>
            <t t-set="url" t-value="'/my/library'"/>
            <t t-set="placeholder_count" t-value="'book_count'"/>
        </t>

    </xpath>
</template>
```

---

## 5. Sistema de Assets

### Declaración en __manifest__.py

```python
'assets': {
    # Bundle para el frontend (portal/website)
    'web.assets_frontend': [
        'mi_modulo/static/src/css/estilos.css',
        'mi_modulo/static/src/js/scripts.js',
    ],

    # Bundle para el backend
    'web.assets_backend': [
        'mi_modulo/static/src/css/backend.css',
    ],

    # SCSS (se compila automáticamente)
    'web.assets_frontend': [
        'mi_modulo/static/src/scss/variables.scss',
        'mi_modulo/static/src/scss/main.scss',
    ],
},
```

### Estructura de Archivos Estáticos

```
mi_modulo/
└── static/
    └── src/
        ├── css/
        │   └── library_portal.css
        ├── scss/
        │   └── library_portal.scss
        ├── js/
        │   └── library_portal.js
        ├── xml/
        │   └── templates.xml  # Para OWL
        └── img/
            └── default_book.png
```

### Bundles Disponibles

| Bundle | Contexto | Uso |
|--------|----------|-----|
| `web.assets_frontend` | Portal/Website | CSS/JS público |
| `web.assets_backend` | Backend | CSS/JS administrativo |
| `web.assets_common` | Ambos | Compartido |

---

## 6. CSS y Estilos

### Bootstrap 5 en Odoo 17

Odoo 17 incluye Bootstrap 5. Puedes usar todas sus clases.

```html
<!-- Grid -->
<div class="row">
    <div class="col-md-4">...</div>
    <div class="col-md-8">...</div>
</div>

<!-- Cards -->
<div class="card">
    <div class="card-header">Título</div>
    <div class="card-body">Contenido</div>
</div>

<!-- Badges -->
<span class="badge bg-success">Disponible</span>
<span class="badge bg-warning">Advertencia</span>
<span class="badge bg-danger">Error</span>

<!-- Alerts -->
<div class="alert alert-info">Información</div>

<!-- Buttons -->
<button class="btn btn-primary">Primario</button>
<button class="btn btn-outline-secondary">Secundario</button>
```

### Variables CSS Personalizadas

```css
/* Definir variables */
:root {
    --library-primary: #2c3e50;
    --library-secondary: #3498db;
    --library-spacing: 1rem;
}

/* Usar variables */
.library-card {
    background-color: var(--library-primary);
    padding: var(--library-spacing);
}
```

### Convenciones de Nombrado

```css
/* Prefijo del módulo para evitar conflictos */
.library-book-card { }
.library-search-bar { }
.library-loan-table { }

/* BEM (Block Element Modifier) */
.library-card { }              /* Bloque */
.library-card__header { }      /* Elemento */
.library-card--featured { }    /* Modificador */
```

### Media Queries Responsivas

```css
/* Mobile first */
.library-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
}

/* Tablets */
@media (min-width: 768px) {
    .library-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Desktop */
@media (min-width: 1024px) {
    .library-grid {
        grid-template-columns: repeat(4, 1fr);
    }
}
```

---

## 7. JavaScript en el Portal

### Estructura Básica

```javascript
// Objeto principal del módulo
const LibraryPortal = {
    // Configuración
    config: {
        searchDelay: 300,
    },

    // Métodos
    init() {
        this.initSearch();
        this.initAnimations();
    },

    initSearch() {
        // ...
    },

    initAnimations() {
        // ...
    },
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    LibraryPortal.init();
});
```

### Llamadas JSON-RPC

```javascript
/**
 * JSON-RPC es el protocolo de comunicación de Odoo.
 * Formato de petición:
 * {
 *   "jsonrpc": "2.0",
 *   "method": "call",
 *   "params": { ... },
 *   "id": número
 * }
 */
async function jsonRpc(url, params = {}) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'call',
            params: params,
            id: Math.random() * 1000000 | 0,
        }),
    });

    const data = await response.json();

    if (data.error) {
        throw new Error(data.error.message);
    }

    return data.result;
}

// Uso
const result = await jsonRpc('/library/search', {
    query: 'Python',
    limit: 10,
});
console.log(result.books);
```

### Debounce para Búsquedas

```javascript
/**
 * Debounce evita llamadas excesivas al servidor.
 * Espera a que el usuario deje de escribir.
 */
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Uso
const searchInput = document.querySelector('#search');

const performSearch = debounce(async (query) => {
    const results = await jsonRpc('/library/search', { query });
    renderResults(results);
}, 300); // Espera 300ms

searchInput.addEventListener('input', (e) => {
    performSearch(e.target.value);
});
```

### Seguridad: Escapar HTML

```javascript
/**
 * SIEMPRE escapar datos antes de insertarlos en el DOM.
 * Previene ataques XSS.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ❌ PELIGROSO
element.innerHTML = `<h1>${userInput}</h1>`;

// ✅ SEGURO
element.innerHTML = `<h1>${escapeHtml(userInput)}</h1>`;

// ✅ MÁS SEGURO (usando DOM)
const h1 = document.createElement('h1');
h1.textContent = userInput;
element.appendChild(h1);
```

---

## 8. Análisis del Código del Módulo

### Estructura del Módulo

```
solt_library_portal_frontend/
├── __manifest__.py
├── __init__.py
├── views/
│   ├── portal_templates.xml        # Templates base y componentes
│   ├── portal_book_templates.xml   # Páginas de libros
│   ├── portal_loan_templates.xml   # Páginas de préstamos
│   └── portal_member_templates.xml # Página de perfil
└── static/
    └── src/
        ├── css/
        │   └── library_portal.css
        └── js/
            └── library_portal.js
```

### Análisis: portal_templates.xml

| Template | Tipo | Propósito |
|----------|------|-----------|
| `portal_my_home_library` | Herencia | Agrega secciones al portal |
| `portal_breadcrumb_library` | Herencia | Migas de pan |
| `portal_sidebar_library` | Herencia | Enlaces en sidebar |
| `book_card` | Componente | Tarjeta de libro reutilizable |
| `loan_status_badge` | Componente | Badge de estado de préstamo |
| `search_bar` | Componente | Barra de búsqueda |
| `search_filters` | Componente | Filtros de búsqueda |
| `pagination_component` | Componente | Paginación |

### Análisis: portal_book_templates.xml

```xml
<!-- Página del catálogo -->
<template id="portal_my_library">
    <t t-call="portal.portal_layout">
        <!-- Barra de búsqueda -->
        <t t-call="solt_library_portal_frontend.search_bar"/>

        <!-- Filtros -->
        <t t-call="solt_library_portal_frontend.search_filters"/>

        <!-- Grid de libros -->
        <t t-foreach="books" t-as="book">
            <t t-call="solt_library_portal_frontend.book_card"/>
        </t>

        <!-- Paginación -->
        <t t-call="solt_library_portal_frontend.pagination_component"/>
    </t>
</template>
```

### Análisis: library_portal.css

```css
/* Variables personalizadas */
:root {
    --library-primary: #2c3e50;
    --library-shadow: 0 4px 8px rgba(0,0,0,0.15);
    --library-transition: all 0.3s ease;
}

/* Tarjetas con hover effect */
.library-book-card {
    transition: var(--library-transition);
}
.library-book-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--library-shadow);
}

/* Responsive */
@media (max-width: 767.98px) {
    .book-cover-container { height: 150px; }
}

/* Accesibilidad */
@media (prefers-reduced-motion: reduce) {
    .library-book-card { animation: none; }
}
```

### Análisis: library_portal.js

```javascript
const LibraryPortal = {
    // Búsqueda en tiempo real
    initSearch() { ... },

    // Verificar disponibilidad cada 30s
    initAvailabilityCheck() { ... },

    // Cargar estadísticas del miembro
    initMemberStats() { ... },

    // Animaciones de entrada
    initAnimations() { ... },
};
```

---

## 9. Buenas Prácticas

### Templates

1. **Usar componentes reutilizables**
```xml
<!-- Definir una vez -->
<template id="badge_disponibilidad">
    <span t-attf-class="badge bg-#{tipo}">
        <t t-esc="texto"/>
    </span>
</template>

<!-- Usar muchas veces -->
<t t-call="mi_modulo.badge_disponibilidad">
    <t t-set="tipo" t-value="'success'"/>
    <t t-set="texto" t-value="'Disponible'"/>
</t>
```

2. **Escapar siempre datos del usuario**
```xml
<!-- ✅ Correcto -->
<span t-esc="usuario_input"/>

<!-- ❌ Peligroso (solo para contenido confiable) -->
<span t-raw="html_confiable"/>
```

3. **Usar clases semánticas**
```xml
<!-- ✅ Semántico -->
<div class="library-book-card library-book-card--featured">

<!-- ❌ No semántico -->
<div class="div1 blue-bg big-text">
```

### CSS

1. **Mobile First**
```css
/* Base (móvil) */
.grid { grid-template-columns: 1fr; }

/* Tablet+ */
@media (min-width: 768px) {
    .grid { grid-template-columns: repeat(2, 1fr); }
}
```

2. **Variables CSS**
```css
:root {
    --color-primary: #007bff;
}
.btn-primary {
    background: var(--color-primary);
}
```

3. **Accesibilidad**
```css
/* Respetar preferencias del usuario */
@media (prefers-reduced-motion: reduce) {
    * { animation: none !important; }
}

@media (prefers-contrast: high) {
    .badge { border: 2px solid; }
}
```

### JavaScript

1. **Evitar jQuery cuando sea posible**
```javascript
// ✅ Vanilla JS
document.querySelector('.btn').addEventListener('click', handler);

// ⚠️ jQuery (más pesado)
$('.btn').click(handler);
```

2. **Async/Await para llamadas asíncronas**
```javascript
// ✅ Limpio y legible
async function loadBooks() {
    try {
        const result = await jsonRpc('/library/search', {});
        renderBooks(result.books);
    } catch (error) {
        showError(error.message);
    }
}
```

3. **Validar datos del servidor**
```javascript
function renderBook(book) {
    // Validar que existen los campos esperados
    if (!book || !book.name) {
        console.error('Datos de libro inválidos');
        return;
    }
    // ...
}
```

---

## 10. Ejercicios Prácticos

### Ejercicio 1: Nuevo Componente

**Objetivo:** Crear un componente de "Autor" reutilizable.

```xml
<!-- views/portal_templates.xml -->

<template id="author_card">
    <!-- TODO: Implementar tarjeta de autor -->
    <!-- Debe mostrar: avatar, nombre, nacionalidad, número de libros -->
</template>
```

### Ejercicio 2: Modificar Estilos

**Objetivo:** Agregar un modo oscuro al portal.

```css
/* static/src/css/library_portal.css */

/* TODO: Implementar estilos para modo oscuro */
@media (prefers-color-scheme: dark) {
    /* ... */
}
```

### Ejercicio 3: Funcionalidad JavaScript

**Objetivo:** Implementar un "favoritos" que persista en localStorage.

```javascript
// static/src/js/library_portal.js

const Favorites = {
    // TODO: Implementar
    // - add(bookId)
    // - remove(bookId)
    // - getAll()
    // - isFavorite(bookId)
};
```

### Ejercicio 4: Herencia de Template

**Objetivo:** Agregar un banner promocional al catálogo.

```xml
<!-- views/portal_book_templates.xml -->

<template id="catalog_promo_banner"
          inherit_id="solt_library_portal_frontend.portal_my_library">
    <!-- TODO: Agregar banner antes del grid de libros -->
</template>
```

---

## Resumen de la Capacitación

### Templates QWeb
- ✅ `t-esc` para texto seguro
- ✅ `t-if`/`t-elif`/`t-else` para condicionales
- ✅ `t-foreach` para iteraciones
- ✅ `t-att-*` y `t-attf-*` para atributos dinámicos
- ✅ `t-call` para componentes reutilizables

### Herencia
- ✅ `inherit_id` para extender templates
- ✅ XPath para localizar elementos
- ✅ Posiciones: inside, before, after, replace

### Assets
- ✅ Declarar en `__manifest__.py`
- ✅ `web.assets_frontend` para portal
- ✅ Bootstrap 5 incluido

### CSS
- ✅ Prefijos de módulo para evitar conflictos
- ✅ Variables CSS para consistencia
- ✅ Media queries para responsive

### JavaScript
- ✅ JSON-RPC para comunicación con servidor
- ✅ Debounce para optimizar búsquedas
- ✅ Escapar HTML para seguridad

---

## Referencias

- [Documentación Oficial - QWeb Templates](https://www.odoo.com/documentation/17.0/developer/reference/frontend/qweb.html)
- [Documentación Oficial - Assets](https://www.odoo.com/documentation/17.0/developer/reference/frontend/assets.html)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.0/)
