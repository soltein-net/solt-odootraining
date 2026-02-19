# -*- coding: utf-8 -*-
{
    'name': 'Library Portal Frontend',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Frontend para el portal de biblioteca',
    'description': """
        Módulo de capacitación - Parte Frontend
        =======================================

        Este módulo implementa la interfaz visual del portal de biblioteca,
        incluyendo templates QWeb, estilos CSS y JavaScript.

        Características:
        ----------------
        * Templates QWeb para páginas del portal
        * Estilos CSS personalizados
        * JavaScript para interactividad
        * Integración con el layout del portal de Odoo

        Temas de capacitación:
        ----------------------
        * Templates QWeb y herencia de vistas
        * Sistema de assets de Odoo 17
        * Estructura del portal de Odoo
        * Componentes frontend reutilizables
        * SCSS y JavaScript en Odoo
    """,
    'author': 'Soltein SA de CV',
    'website': 'https://www.soltein.com',
    'license': 'LGPL-3',
    'depends': [
        'solt_library_portal_backend',  # Hereda del backend
        'web',
    ],
    'data': [
        'views/portal_templates.xml',
        'views/portal_book_templates.xml',
        'views/portal_loan_templates.xml',
        'views/portal_member_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'solt_library_portal_frontend/static/src/css/library_portal.css',
            'solt_library_portal_frontend/static/src/js/library_portal.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
