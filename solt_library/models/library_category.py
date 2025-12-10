# -*- coding: utf-8 -*-
from odoo import models, fields, api


class LibraryCategory(models.Model):
    _name = 'library.category'
    _description = 'Book Category'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char('Name', required=True)
    complete_name = fields.Char(
        'Complete Name',
        compute='_compute_complete_name',
        recursive=True,
        store=True
    )
    parent_id = fields.Many2one(
        'library.category',
        string='Parent Category',
        index=True,
        ondelete='cascade'
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        'library.category',
        'parent_id',
        string='Subcategories'
    )
    book_ids = fields.One2many(
        'library.book',
        'category_id',
        string='Books'
    )
    book_count = fields.Integer(
        compute='_compute_book_count',
        string='Book Count'
    )

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = f'{category.parent_id.complete_name} / {category.name}'
            else:
                category.complete_name = category.name

    @api.depends('book_ids')
    def _compute_book_count(self):
        for category in self:
            category.book_count = len(category.book_ids)
