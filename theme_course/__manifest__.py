{
    'name': 'Course Theme',
    'description': 'Colores claros, texto fino, diseño limpio y nítido.',
    'category': 'Theme/Corporate',
    'summary': 'Servicios, Empresa, Diseño, Tecnología, Robótica, Informática, TI, Blogs',
    'sequence': 110,
    'version': '17.0.1.0.1',
    'data': [
        # Vievs
        'views/theme_customize.xml',
        # Templates
        'templates/snippets/s_features_columns.xml',
        'templates/snippets.xml'
    ],
    'images': [
        'theme_course/static/description/course_poster.jpg',
        'theme_course/static/description/course_screenshot.png',
    ],
    'images_preview_theme': {
    },
    'depends': ['website'],
    'license': 'LGPL-3',
    'assets': {
        'web._assets_primary_variables': [
            'theme_course/static/src/scss/primary_variables.scss'
        ],
        'web._assets_frontend_helpers': [
            'theme_course/static/src/scss/bootstrap_overriden.scss',
        ],
        'website.assets_wysiwyg': [
            'theme_course/static/src/js/snippets.options.js',
        ],
        'web.assets_frontend': [
            'theme_course/static/src/scss/fonts.scss',
            'theme_course/static/src/scss/custom_spacing.scss'
        ],
    }
}
