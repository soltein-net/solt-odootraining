from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseContract(models.Model):
    _name = 'purchase.contract'
    _description = 'Contrato de compra'

    name = fields.Char(string='Nombre del Contrato', required=True)
    description = fields.Text(string='Descripción')
    purchase_order_id = fields.Many2one('purchase.order', string='Pedido de Compra')
    start_date = fields.Date(string='Fecha de Inicio', required=True)
    end_date = fields.Date(string='Fecha de Fin', required=True)

    @api.model
    def create(self, vals):
        # Validar fechas
        if vals.get('start_date') and vals.get('end_date') and vals['start_date'] > vals['end_date']:
            raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")
        # Agregar descripción automática si no existe
        if not vals.get('description'):
            vals['description'] = f"Contrato generado automáticamente: {vals['name']}"
        return super(PurchaseContract, self).create(vals)

    def write(self, vals):
        for record in self:
            if 'end_date' in vals and record.end_date < fields.Date.today():
                raise ValidationError("No puedes modificar un contrato que ya expiró.")
        return super(PurchaseContract, self).write(vals)

    def unlink(self):
        for record in self:
            if record.start_date <= fields.Date.today() <= record.end_date:
                raise ValidationError(f"No puedes eliminar un contrato activo: {record.name}")
            # Registrar eliminación
            self.env['ir.logging'].create({
                'name': 'Eliminación de Contrato',
                'type': 'server',
                'dbname': self.env.cr.dbname,
                'message': f"El contrato '{record.name}' fue eliminado.",
                'level': 'warning',
            })
        return super(PurchaseContract, self).unlink()