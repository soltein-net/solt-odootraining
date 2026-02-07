# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_key = fields.Char(string="API Key Solt Library")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            api_key=params.get_param('solt_library.api_url', default=''),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('solt_library.api_url', self.api_key or '')

    # Establecer un parámetro
    #self.env['ir.config_parameter'].sudo().set_param('mi_modulo.api_key', 'mi_clave_secreta')

    # Obtener un parámetro
    #api_key = self.env['ir.config_parameter'].sudo().get_param('mi_modulo.api_key')

    # Obtener con valor por defecto
    #api_key = self.env['ir.config_parameter'].sudo().get_param('mi_modulo.api_key', default='valor_por_defecto')1

    # Obtener parámetro
    #get_param(key, default=False)

    # Establecer parámetro
    #set_param(key, value)

    # Buscar parámetros
    #search([('key', '=', 'mi_clave')])

    # Eliminar parámetro
    #unlink()