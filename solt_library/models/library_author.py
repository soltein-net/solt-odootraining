# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class LibraryAuthor(models.Model):
    _name = 'library.author'
    _description = 'Book Author'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'avatar.mixin']
    _order = 'name'

    name = fields.Char('Name', required=True, tracking=True)
    birth_date = fields.Date('Birth Date')
    death_date = fields.Date('Death Date')
    biography = fields.Html('Biography')
    nationality = fields.Char('Nationality')
    website = fields.Char('Website')
    book_ids = fields.Many2many(
        'library.book',
        'library_book_author_rel',
        'author_id',
        'book_id',
        string='Books'
    )
    book_count = fields.Integer(
        compute='_compute_book_count',
        string='Book Count'
    )
    age = fields.Integer(compute='_compute_age', string='Age')

    @api.depends('book_ids')
    def _compute_book_count(self):
        for author in self:
            author.book_count = len(author.book_ids)

    @api.depends('birth_date', 'death_date')
    def _compute_age(self):
        today = date.today()
        for author in self:
            if author.birth_date:
                end_date = author.death_date or today
                author.age = end_date.year - author.birth_date.year
            else:
                author.age = 0

    @api.constrains('birth_date', 'death_date')
    def _check_dates(self):
        for author in self:
            if author.death_date and author.birth_date:
                if author.death_date < author.birth_date:
                    raise models.ValidationError(
                        'Death date cannot be earlier than birth date'
                    )