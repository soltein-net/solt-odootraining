# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CryptoToken(models.Model):
    _name = 'crypto.token'
    _description = 'Crypto Token'

    name = fields.Char(string='Token Name', required=True)
    symbol = fields.Char(string='Token symbol', required=True)

    description = fields.Text(string='Description')

    layer = fields.Selection([('layer1', 'Layer 1'), ('layer2', 'Layer 3'), ('layer3', 'Layer 3')], string='Layer')
    current_price = fields.Float(string='Current Price in USDT')
