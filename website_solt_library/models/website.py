from odoo import models, _
from odoo.addons.http_routing.models.ir_http import url_for

class Website(models.Model):
    _inherit = "website"

    def get_suggested_controllers(self):
        suggested_controllers = super().get_suggested_controllers()
        suggested_controllers.append((_('Books'), url_for('/libros'), 'website_solt_library'))
        return suggested_controllers

    def _search_get_details(self, search_type, order, options):
        result = super()._search_get_details(search_type, order, options)
        if search_type in ['books', 'books_only', 'all']:
            result.append(self.env['library.book']._search_get_detail(self, order, options))
        return result