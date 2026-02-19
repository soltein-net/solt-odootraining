# -*- coding: utf-8 -*-
{
    'name': 'Library Portal Backend',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Backend para personalización del portal de biblioteca',
    'description': """
        Módulo de capacitación - Parte Backend
        =======================================

        Este módulo implementa la lógica de backend necesaria para exponer
        los datos de la biblioteca a través del portal web de Odoo.

        Características:
        ----------------
        * Controladores HTTP para acceso al portal
        * Rutas personalizadas para consulta de catálogo
        * Extensión de modelos para acceso portal
        * Seguridad y validación de acceso
        * API para consulta de libros, autores y préstamos

        Temas de capacitación:
        ----------------------
        * Arquitectura de portal en Odoo 17
        * Definición de controladores HTTP
        * Rutas y decoradores de Odoo
        * Acceso a datos desde el portal
        * Seguridad en el contexto del portal
    """,
    'author': 'Soltein SA de CV',
    'website': 'https://www.soltein.com',
    'license': 'LGPL-3',
    'depends': [
        'solt_library',
        'portal',
        'website'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/portal_security.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
