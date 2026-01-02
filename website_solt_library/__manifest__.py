# -*- coding: utf-8 -*-
{
    'name': 'Website Library',
    'description': 'Modulo de sitio web para libreria',
    'version': '17.0.1.0.0',
    'summary': 'Website, Cursos, Educación, Libros',
    'author': 'Soltein SA de CV',
    'website': 'https://soltein.mx',
    'category': 'Website/Tools',
    'depends': ['website', 'solt_library'],
    'data': [
        'data/snippet-books-data.xml',
        'templates/header.xml',
        'templates/footer.xml',
        'templates/snippets/s_synamic_snippet_books.xml',
        'templates/snippets.xml'
    ],
    'assets': {
        'web.assets_frontend': [
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
