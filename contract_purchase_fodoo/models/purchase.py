from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_recurrent = fields.Boolean(string='Compra Recurrente', default=False)

    def button_confirm(self):
        # Llamamos a la funcionalidad estándar
        super(PurchaseOrder, self).button_confirm()

        # Creamos una compra en borrador si es recurrente
        for order in self:
            if order.is_recurrent:
                self.create_recurring_purchase(order)

    def create_recurring_purchase(self, original_order):
        """
        Crea una compra recurrente en estado borrador basada en la orden confirmada.
        """
        new_order = self.create({
            'partner_id': original_order.partner_id.id,
            'order_line': [(0, 0, {
                'name': line.name,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_qty': line.product_qty,
                'price_unit': line.price_unit,
                'date_planned': line.date_planned,
            }) for line in original_order.order_line],
            'is_recurrent': True,  # Heredamos la propiedad recurrente
        })
        return new_order


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    extra_amount = fields.Float(string='Monto Extra', compute='_compute_extra_amount', store=True)
    # 2. Operadores y Funciones
    extended_subtotal = fields.Float(string='Subtotal Extendido', compute='_compute_extended_subtotal', store=True)

    @api.depends('product_id', 'product_id.type')
    def _compute_extra_amount(self):
        for line in self:
            if line.product_id.type == 'service':
                line.extra_amount = line.price_unit * 0.1  # Aplica un 10% como monto extra
            else:
                line.extra_amount = 0

   #2. Operadores y Funciones
    @api.depends('price_subtotal', 'extra_amount')
    def _compute_extended_subtotal(self):
        for line in self:
            line.extended_subtotal = line.price_subtotal + line.extra_amount
