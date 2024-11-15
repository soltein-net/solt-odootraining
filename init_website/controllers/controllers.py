# -*- coding: utf-8 -*-
from odoo import http


class InitWebsite(http.Controller):
    @http.route('/mi_pagina', auth='public', website=True)
    def mostrar_pagina(self, **kw):
        return http.request.render('init_website.mi_plantilla', {})
