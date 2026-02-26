from odoo import api, fields, models
from odoo.addons.http_routing.models.ir_http import unslug


class LibraryBook(models.Model):
    _name = 'library.loan'
    _inherit = ['library.loan', 'website.published.multi.mixin']

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    name = fields.Char(string='Name', readonly=True, related="reference")
    description = fields.Html(string='Description')

    @api.depends_context('lang')
    def _compute_website_url(self):
        for record in self:
            record.website_url = f'/my/loans/{record.id}'