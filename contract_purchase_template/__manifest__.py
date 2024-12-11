{
    'name': 'Mi Modulo Personalizado',
    'version': '1.0',
    'category': 'Custom',
    'author': 'Tu Nombre',
    'depends': ['purchase', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_contract_views.xml',
        'views/purchase_order_line_views.xml',
        'views/purchase_order_views.xml',

    ],
    'installable': True,
    'application': False,
}
