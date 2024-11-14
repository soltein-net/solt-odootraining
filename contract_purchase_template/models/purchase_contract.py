from odoo import models, fields, api


class PurchaseContract(models.Model):
    _name = 'purchase.contract'
    _description = 'Contrato de compra'

    name = fields.Char(string='Nombre del Contrato', required=True)
    description = fields.Text(string='Descripción')
    purchase_order_id = fields.Many2one('purchase.order', string='Pedido de Compra')

