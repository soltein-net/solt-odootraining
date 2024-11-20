{
    'name': 'Mi Crypto Wallet',
    'description': 'Simula una billetera de criptomonedas',
    'version': '0.1.0',
    'category': 'Custom',
    'author': 'Odoo Student',
    'website': 'https://www.soltein.mx',
    'license': 'AGPL-3',
    'depends': ['base', 'product'],
    'data': [
        # security
        'security/ir.model.access.csv',

        # views
        'views/crypto_token_views.xml',
        'views/crypto_wallet_views.xml',

        # menu
        'views/crypto_wallet_menu.xml',


    ],
    'installable': True,
    'application': True,
}
