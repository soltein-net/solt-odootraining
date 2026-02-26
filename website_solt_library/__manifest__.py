# -*- coding: utf-8 -*-
{
    'name': 'Website Library',
    'description': 'Modulo de sitio web para libreria',
    'version': '17.0.1.0.0',
    'summary': 'Website, Cursos, Educación, Libros',
    'author': 'Soltein SA de CV',
    'website': 'https://soltein.mx',
    'category': 'Website/Tools',
    'depends': ['website_profile', 'website_common', 'solt_library'],
    "data": [
        "data/snippet-books-data.xml",
        "security/ir.model.access.csv",
        "views/library_book.xml",
        "templates/authors.xml",
        "templates/book_detail.xml",
        "templates/books.xml",
        "templates/footer.xml",
        "templates/header.xml",
        "templates/loans.xml",
        "templates/members.xml",
        "templates/snippets.xml",
        "templates/snippets/s_synamic_snippet_books.xml"
    ],
    'assets': {
        'web.assets_frontend': [
            'website_solt_library/static/src/scss/book_card.scss',
            'website_solt_library/static/src/snippets/s_synamic_snippet_books/000.js'
        ],
        'website.assets_wysiwyg': [
            'website_solt_library/static/src/snippets/s_synamic_snippet_books/options.js',
        ]
    },
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
