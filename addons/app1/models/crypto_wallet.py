# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CryptoWallet(models.Model):
    _name = 'crypto.wallet'
    _description = 'Crypot Wallet'

    name = fields.Char(string='name', compute='_compute_name')
    description = fields.Text(string='Descripción')
    partner_id = fields.Many2one('res.partner', string='Wallet Owner', required=True)

    usdt_balance = fields.Float(string='USDT Balance', default=0.0, compute='_compute_usdt_balance')

    tokens = fields.One2many('crypto.wallet.tokens', 'wallet_id', string='Tokens')

    @api.depends('tokens')
    def _compute_usdt_balance(self):
        for record in self:
            #: set the balance to the sum of the total of each token
            record.usdt_balance = sum(record.tokens.mapped('total_usdt_value'))

    @api.depends('partner_id')
    def _compute_name(self):
        for record in self:
            #: set the name of the wallet to the string 'name of the partner's wallet'
            if record.partner_id and record.partner_id.name:
                record.name = record.partner_id.name + "'s Wallet"
            else:
                record.name = 'Wallet'


class CryptoTokenList(models.Model):
    _name = 'crypto.wallet.tokens'
    _description = 'Crypto Wallet Token List'

    wallet_id = fields.Many2one('crypto.wallet', string='Wallet', required=True)
    token_id = fields.Many2one('crypto.token', string='Token', required=True)
    quantity = fields.Float(string='Quantity', required=True)

    buy_price = fields.Float(string='Bought Price', required=True)
    current_price = fields.Float(string='Current Price', related='token_id.current_price')

    total_usdt_value = fields.Float(string='Total', compute='_compute_total')
    result = fields.Float(string='Result', compute='_compute_result')

    @api.depends('quantity', 'current_price')
    def _compute_total(self):
        for record in self:
            #: set the total to the quantity times the price
            record.total_usdt_value = record.quantity * record.current_price

    @api.depends('total_usdt_value', 'current_price')
    def _compute_result(self):
        for record in self:
            #: set the result to the total minus the adquisition value
            adquisition_value = record.quantity * record.buy_price
            record.result = record.total_usdt_value - adquisition_value
