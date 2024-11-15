# -*- coding: utf-8 -*-
{
    'name': "init_website",

    'summary': """
        Módulo personalizado para gestionar el frontend""",

    'description': """
        Módulo personalizado para gestionar el frontend
    """,

    'author': "Soltein SA de CV",
    'website': "http://soltein.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['website'],

    # always loaded
    'data': [
        'data/website_data.xml',
        'views/templates.xml',

    ],

}