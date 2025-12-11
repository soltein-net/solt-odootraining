# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta, datetime


class LibraryLoan(models.Model):
    _name = 'library.loan'
    _description = 'Book Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'loan_date desc'
    _rec_name = 'reference'

    reference = fields.Char(
        'Reference',
        readonly=True,
        copy=False,
        default='New'
    )
    member_id = fields.Many2one(
        'library.member',
        string='Member',
        required=True,
        tracking=True,
        domain=[('state', '=', 'active')]
    )
    book_id = fields.Many2one(
        'library.book',
        string='Book',
        required=True,
        tracking=True,
        domain=[('state', '!=', 'unavailable')]
    )

    # Book info (denormalized for history)
    book_isbn = fields.Char(related='book_id.isbn', store=True)
    book_authors = fields.Char(
        compute='_compute_book_authors',
        store=True
    )

    loan_date = fields.Date(
        'Loan Date',
        default=fields.Date.today,
        required=True,
        tracking=True
    )
    expected_return_date = fields.Date(
        'Expected Return Date',
        compute='_compute_return_date',
        store=True,
        tracking=True
    )
    actual_return_date = fields.Date(
        'Actual Return Date',
        tracking=True
    )

    days_overdue = fields.Integer(
        'Days Overdue',
        compute='_compute_days_overdue',
        store=True
    )
    late_fee = fields.Monetary(
        'Late Fee',
        compute='_compute_late_fee',
        store=True,
        currency_field='currency_id'
    )
    fee_paid = fields.Boolean('Fee Paid', tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('loaned', 'Loaned'),
        ('returned', 'Returned'),
        ('lost', 'Lost'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    notes = fields.Text('Notes')

    user_id = fields.Many2one(
        'res.users',
        string='Librarian',
        default=lambda self: self.env.user,
        tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'library.loan'
                ) or 'New'
        return super().create(vals_list)

    @api.depends('book_id.author_ids')
    def _compute_book_authors(self):
        for loan in self:
            if loan.book_id and loan.book_id.author_ids:
                loan.book_authors = ', '.join(
                    loan.book_id.author_ids.mapped('name')
                )
            else:
                loan.book_authors = ''

    @api.depends('loan_date', 'member_id.loan_days')
    def _compute_return_date(self):
        for loan in self:
            if loan.loan_date and loan.member_id:
                days = loan.member_id.loan_days or 21
                loan.expected_return_date = (
                        loan.loan_date + timedelta(days=days)
                )
            else:
                loan.expected_return_date = False

    @api.depends('expected_return_date', 'actual_return_date', 'state')
    def _compute_days_overdue(self):
        today = date.today()
        for loan in self:
            if loan.state not in ['loaned', 'returned', 'lost']:
                loan.days_overdue = 0
                continue

            if not loan.expected_return_date:
                loan.days_overdue = 0
                continue

            end_date = loan.actual_return_date or today
            if end_date > loan.expected_return_date:
                loan.days_overdue = (
                        end_date - loan.expected_return_date
                ).days
            else:
                loan.days_overdue = 0

    @api.depends('days_overdue')
    def _compute_late_fee(self):
        FEE_PER_DAY = 0.50  # Configurable
        for loan in self:
            loan.late_fee = loan.days_overdue * FEE_PER_DAY

    @api.constrains('member_id', 'state')
    def _check_max_loans(self):
        for loan in self:
            if loan.state == 'loaned':
                active_count = self.search_count([
                    ('member_id', '=', loan.member_id.id),
                    ('state', '=', 'loaned'),
                ])
                if active_count > loan.member_id.max_loans:
                    raise ValidationError(
                        f'Member {loan.member_id.name} has reached '
                        f'the limit of {loan.member_id.max_loans} loans'
                    )

    @api.constrains('book_id', 'state')
    def _check_availability(self):
        for loan in self:
            if loan.state == 'loaned':
                if loan.book_id.available_qty < 0:
                    raise ValidationError(
                        f'No available copies of "{loan.book_id.name}"'
                    )

    @api.onchange('member_id')
    def _onchange_member(self):
        if self.member_id:
            if self.member_id.state != 'active':
                return {
                    'warning': {
                        'title': 'Inactive Member',
                        'message': f'Member {self.member_id.name} is not active'
                    }
                }
            if self.member_id.pending_fees > 0:
                return {
                    'warning': {
                        'title': 'Pending Fees',
                        'message': f'This member has ${self.member_id.pending_fees} in pending fees'
                    }
                }

    @api.onchange('book_id')
    def _onchange_book(self):
        if self.book_id:
            if self.book_id.available_qty <= 0:
                return {
                    'warning': {
                        'title': 'Not Available',
                        'message': f'"{self.book_id.name}" has no available copies'
                    }
                }

    def action_confirm(self):
        for loan in self:
            if loan.state != 'draft':
                raise UserError('Only draft loans can be confirmed')
            if loan.member_id.state != 'active':
                raise UserError(
                    f'Member {loan.member_id.name} is not active'
                )
            if loan.book_id.available_qty <= 0:
                raise UserError(
                    f'No available copies of "{loan.book_id.name}"'
                )
            loan.write({'state': 'loaned'})
            loan.message_post(
                body=f'📚 Book loaned to {loan.member_id.name}'
            )
            # Schedule follow-up activity
            loan.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=loan.expected_return_date,
                summary=f'Pending return: {loan.book_id.name}',
                user_id=loan.user_id.id
            )

    def action_return(self):
        for loan in self:
            if loan.state != 'loaned':
                raise UserError('Only active loans can be returned')
            loan.write({
                'state': 'returned',
                'actual_return_date': date.today()
            })
            # Mark activities as done
            loan.activity_ids.action_done()

            if loan.days_overdue > 0:
                loan.message_post(
                    body=f'📕 Book returned {loan.days_overdue} days late. '
                         f'Late fee: ${loan.late_fee}'
                )
            else:
                loan.message_post(body='📗 Book returned on time')

    def action_mark_lost(self):
        for loan in self:
            if loan.state != 'loaned':
                raise UserError('Only active loans can be marked as lost')
            loan.write({'state': 'lost'})
            loan.message_post(body='⚠️ Book marked as lost')
            loan.activity_ids.action_done()

    def action_cancel(self):
        for loan in self:
            if loan.state not in ['draft']:
                raise UserError('Only drafts can be cancelled')
            loan.write({'state': 'cancelled'})

    @api.model
    def _cron_check_due_dates(self):
        """Cron job to check overdue loans and send notifications"""
        today = date.today()
        # Loans due today
        due_today = self.search([
            ('state', '=', 'loaned'),
            ('expected_return_date', '=', today)
        ])
        for loan in due_today:
            loan.message_post(
                body='⏰ Loan is due today',
                partner_ids=[loan.member_id.partner_id.id]
            )

        # Overdue loans (3 days)
        three_days_ago = today - timedelta(days=3)
        overdue = self.search([
            ('state', '=', 'loaned'),
            ('expected_return_date', '=', three_days_ago)
        ])
        for loan in overdue:
            loan.message_post(
                body=f'🚨 Loan overdue by 3 days. Accumulated fee: ${loan.late_fee}',
                partner_ids=[loan.member_id.partner_id.id]
            )


    #funciones que extienden las funcionalidades del importador de datos
    @api.model
    def _convert_import_date(self, date_str, fields):
        # Ejemplo: Extiende la conversión de fecha para aceptar otro formato
        print('Converting date:', date_str)
        print('Converting Fields:', fields)
        if date_str:
            try:
                # Intenta el formato original
                return super()._convert_import_date(date_str, fields)
            except Exception:
                try:
                    # Nuevo formato admitido: yyyy/mm/dd
                    return datetime.strptime(date_str, '%Y/%m/%d').date()
                except Exception:
                    return date_str
        return date_str


    @api.model
    def _sanitize_import_reference(self, value, fields):
        print('Sanitizing reference:', value)
        print('Sanitizin Fields:', fields)
        # Ejemplo: Añade un prefijo personalizado a la referencia importada
        value = super()._sanitize_import_reference(value, fields)
        if value:
            return f'IMP-{value}'
        return value

    @api.model
    def _validate_import_book(self, value, fields):
        # Ejemplo: Permite buscar por ISBN además del nombre
        print('Validating book:', value)
        print('Validating Fields:', fields)
        Book = self.env['library.book']
        book = Book.search([('name', '=', value)], limit=1)
        if not book:
            book = Book.search([('isbn', '=', value)], limit=1)
        if not book:
            raise ValidationError(f'El libro "{value}" no existe en el catálogo.')
        return book.id



