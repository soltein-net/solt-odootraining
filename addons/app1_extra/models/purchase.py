from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    extra_amount = fields.Float(string='Monto Extra', compute='_compute_extra_amount', store=True)

    @api.depends('product_id', 'product_id.type')
    def _compute_extra_amount(self):
        for line in self:
            if line.product_id.type == 'service':
                line.extra_amount = line.price_unit * 0.1  # Aplica un 10% como monto extra
            else:
                line.extra_amount = 0
