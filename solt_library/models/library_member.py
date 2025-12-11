# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta
import logging


class LibraryMember(models.Model):
    _name = 'library.member'
    _description = 'Library Member'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'avatar.mixin']
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        required=True,
        ondelete='cascade'
    )
    code = fields.Char(
        'Member Code',
        readonly=True,
        copy=False,
        default='New'
    )
    registration_date = fields.Date(
        'Registration Date',
        default=fields.Date.today,
        required=True
    )
    expiration_date = fields.Date(
        'Expiration Date',
        compute='_compute_expiration_date',
        store=True
    )
    membership_type = fields.Selection([
        ('student', 'Student'),
        ('regular', 'Regular'),
        ('premium', 'Premium'),
        ('lifetime', 'Lifetime'),
    ], string='Membership Type', default='regular', tracking=True)

    max_loans = fields.Integer(
        'Maximum Loans',
        compute='_compute_max_loans'
    )
    loan_days = fields.Integer(
        'Loan Days',
        compute='_compute_loan_days'
    )

    loan_ids = fields.One2many(
        'library.loan',
        'member_id',
        string='Loans'
    )
    active_loan_count = fields.Integer(
        compute='_compute_loan_stats',
        string='Active Loans'
    )
    overdue_loan_count = fields.Integer(
        compute='_compute_loan_stats',
        string='Overdue Loans'
    )
    pending_fees = fields.Monetary(
        compute='_compute_loan_stats',
        string='Pending Fees',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    state = fields.Selection([
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    ], string='Status', default='active', tracking=True)

    notes = fields.Text('Internal Notes')
    active = fields.Boolean(default=True)

    date_member_created = fields.Datetime(
        'Member Created On',
        store=True,
        readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code(
                    'library.member'
                ) or 'New'
        return super().create(vals_list)

    @api.depends('registration_date', 'membership_type')
    def _compute_expiration_date(self):
        for member in self:
            if member.membership_type == 'lifetime':
                member.expiration_date = False
            elif member.registration_date:
                if member.membership_type == 'student':
                    member.expiration_date = member.registration_date + relativedelta(months=6)
                else:
                    member.expiration_date = member.registration_date + relativedelta(years=1)
            else:
                member.expiration_date = False

    @api.depends('membership_type')
    def _compute_max_loans(self):
        limits = {
            'student': 3,
            'regular': 5,
            'premium': 10,
            'lifetime': 15,
        }
        for member in self:
            member.max_loans = limits.get(member.membership_type, 5)

    @api.depends('membership_type')
    def _compute_loan_days(self):
        days = {
            'student': 14,
            'regular': 21,
            'premium': 30,
            'lifetime': 45,
        }
        for member in self:
            member.loan_days = days.get(member.membership_type, 21)

    @api.depends('loan_ids.state', 'loan_ids.late_fee')
    def _compute_loan_stats(self):
        today = date.today()
        for member in self:
            active_loans = member.loan_ids.filtered(
                lambda l: l.state == 'loaned'
            )
            member.active_loan_count = len(active_loans)
            member.overdue_loan_count = len(active_loans.filtered(
                lambda l: l.expected_return_date and l.expected_return_date < today
            ))
            member.pending_fees = sum(
                member.loan_ids.filtered(
                    lambda l: l.state != 'returned' and l.late_fee > 0
                ).mapped('late_fee')
            )

    def action_suspend(self):
        self.write({'state': 'suspended'})
        self.message_post(body='Member suspended')

    def action_activate(self):
        self.write({'state': 'active'})
        self.message_post(body='Member activated')

    def action_view_loans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Loans - {self.name}',
            'res_model': 'library.loan',
            'view_mode': 'tree,form,calendar',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id},
        }

    @api.model
    def _cron_check_expired_memberships(self):
        expired = self.search([
            ('expiration_date', '&lt;', date.today()),
            ('state', '=', 'active'),
            ('membership_type', '!=', 'lifetime')
        ])
        expired.write({'state': 'expired'})

    @api.model
    def load(self, fields, data):
        """
        Override del método load para depurar y validar datos durante la importación.
        Útil para identificar problemas con el campo membership_type.
        """
        _logger = logging.getLogger(__name__)

        # Registrar información sobre la importación
        _logger.info(f"=== Importación de Library Member ===")
        _logger.info(f"Campos a importar: {fields}")
        _logger.info(f"Cantidad de registros: {len(data)}")

        # Si membership_type está en los campos a importar
        if 'membership_type' in fields:
            membership_idx = fields.index('membership_type')
            valid_types = {'student', 'regular', 'premium', 'lifetime'}

            for idx, row in enumerate(data, start=1):
                membership_value = row[membership_idx] if len(row) > membership_idx else None

                if membership_value:
                    # Normalizar el valor (quitar espacios, minúsculas)
                    normalized_value = str(membership_value).strip().lower()

                    _logger.info(f"Fila {idx}: membership_type = '{membership_value}' -> '{normalized_value}'")

                    # Validar si el valor es válido
                    if normalized_value not in valid_types:
                        _logger.warning(
                            f"⚠️ Fila {idx}: Valor inválido '{membership_value}'. "
                            f"Valores permitidos: {valid_types}"
                        )

                    # Corrección automática: reemplazar el valor normalizado
                    row[membership_idx] = normalized_value

        # Llamar al método original de Odoo
        result = super(LibraryMember, self).load(fields, data)

        _logger.info(f"Resultado: {result['ids']} registros creados/actualizados")
        if result.get('messages'):
            _logger.warning(f"Mensajes de importación: {result['messages']}")

        return result

