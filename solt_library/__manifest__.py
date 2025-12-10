# -*- coding: utf-8 -*-
{
    'name': 'Library Management',
    'version': '17.0.1.0.0',
    'category': 'Services',
    'summary': 'Complete library management: books, loans and returns',
    'description': """
                           Library management module that includes:
                           - Book catalog with authors and categories
                           - Member/patron management
                           - Loan and return control
                           - Automatic late fee calculation
                           - Book reservations
                       """,
    'author': 'Soltein SA de CV',
    'website': 'https://soltein.mx/',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'contacts'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/library_sequence.xml',
        'data/library_cron.xml',
        'views/library_category_views.xml',
        'views/library_author_views.xml',
        'views/library_book_views.xml',
        'views/library_member_views.xml',
        'views/library_loan_views.xml',
        'views/library_menus.xml',
        'report/library_loan_report.xml',
        'report/library_loan_template.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
