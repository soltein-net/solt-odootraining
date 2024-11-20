{
    'name': 'Mi Crypto Wallet Extended',
    'version': '1.0',
    'category': 'Custom',
    'author': 'Odoo Student',
    'depends': ['purchase', 'product'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_contract_views.xml',
        'views/purchase_order_line_views.xml',
        'views/purchase_order_views.xml',

    ],
    'installable': True,
    'application': True,
}
