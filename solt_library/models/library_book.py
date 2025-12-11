# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'name'

    name = fields.Char('Title', required=True, tracking=True)
    isbn = fields.Char('ISBN', tracking=True, copy=False)
    description = fields.Text('Description')
    publication_date = fields.Date('Publication Date')
    pages = fields.Integer('Number of Pages')
    publisher = fields.Char('Publisher')
    language = fields.Selection([
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('pt', 'Portuguese'),
        ('other', 'Other'),
    ], string='Language', default='en')

    category_id = fields.Many2one(
        'library.category',
        string='Category',
        required=True,
        tracking=True
    )
    author_ids = fields.Many2many(
        'library.author',
        'library_book_author_rel',
        'book_id',
        'author_id',
        string='Authors',
        required=True
    )

    # Inventory control
    total_qty = fields.Integer(
        'Total Copies',
        default=1,
        tracking=True
    )
    available_qty = fields.Integer(
        'Available Copies',
        compute='_compute_availability',
        store=True
    )
    loaned_qty = fields.Integer(
        'Loaned Copies',
        compute='_compute_availability',
        store=True
    )

    state = fields.Selection([
        ('available', 'Available'),
        ('low_stock', 'Low Stock'),
        ('unavailable', 'Unavailable'),
    ], string='Status', compute='_compute_state', store=True)

    loan_ids = fields.One2many(
        'library.loan',
        'book_id',
        string='Loans'
    )
    active_loan_ids = fields.One2many(
        'library.loan',
        'book_id',
        string='Active Loans',
        domain=[('state', '=', 'loaned')]
    )

    active = fields.Boolean(default=True)
    color = fields.Integer('Color')

    _sql_constraints = [
        ('isbn_unique', 'UNIQUE(isbn)', 'ISBN must be unique'),
        ('qty_positive', 'CHECK(total_qty >= 0)','Total quantity cannot be negative'),
    ]

    @api.depends('total_qty', 'loan_ids.state')
    def _compute_availability(self):
        for book in self:
            loaned = len(book.loan_ids.filtered(
                lambda l: l.state == 'loaned'
            ))
            book.loaned_qty = loaned
            book.available_qty = book.total_qty - loaned
            _logger.info(f'Book {book.name}: Total={book.total_qty}, Loaned={loaned}, Available={book.available_qty}')

    @api.depends('available_qty', 'total_qty')
    def _compute_state(self):
        for book in self:
            if book.available_qty <= 0:
                book.state = 'unavailable'
            elif book.available_qty <= (book.total_qty * 0.2):
                book.state = 'low_stock'
            else:
                book.state = 'available'

    @api.constrains('isbn')
    def _check_isbn(self):
        for book in self:
            if book.isbn:
                isbn_clean = book.isbn.replace('-', '').replace(' ', '')
                if len(isbn_clean) not in [10, 13]:
                    raise ValidationError(
                        'ISBN must have 10 or 13 digits'
                    )
                if not isbn_clean.replace('X', '').isdigit():
                    raise ValidationError(
                        'ISBN can only contain numbers and X'
                    )

    @api.onchange('category_id')
    def _onchange_category(self):
        if self.category_id:
            return {
                'domain': {
                    'author_ids': [('book_ids.category_id', '=', self.category_id.id)]
                }
            }

    def action_view_loans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Loans - {self.name}',
            'res_model': 'library.loan',
            'view_mode': 'tree,form',
            'domain': [('book_id', '=', self.id)],
            'context': {'default_book_id': self.id},
        }

    #TODO crear una funcion apra agregar 10 paginas al libro al momento de importar los datos
    @api.model
    def create(self, vals):
        if 'pages' in vals:
            vals['pages'] += 10
        return super(LibraryBook, self).create(vals)

