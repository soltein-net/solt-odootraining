from odoo import api, models


class LibraryBook(models.Model):
    _name = 'library.book'
    _inherit = ['library.book', 'website.published.multi.mixin']

    @api.depends_context('lang')
    def _compute_website_url(self):
        for record in self:
            record.website_url = f'/libros/{record.id}'