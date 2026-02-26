from odoo import models


class LibraryCategory(models.Model):
    _name = 'library.category'
    _inherit = ['library.category', 'website.multi.mixin']
