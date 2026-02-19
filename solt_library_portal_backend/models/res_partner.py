# -*- coding: utf-8 -*-
"""
================================================================================
EXTENSIÓN DEL MODELO RES.PARTNER PARA LA BIBLIOTECA
================================================================================

Este archivo extiende el modelo res.partner para agregar campos
relacionados con la biblioteca.

CONCEPTOS CLAVE PARA LA CAPACITACIÓN:
-------------------------------------

1. EXTENSIÓN DE MODELOS CORE:
   - Podemos extender modelos de Odoo base
   - Útil para agregar funcionalidad transversal
   - Mantiene la integridad del modelo original
"""

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # =========================================================================
    # CAMPOS RELACIONADOS CON LA BIBLIOTECA
    # =========================================================================

    # Relación inversa con library.member
    library_member_ids = fields.One2many(
        'library.member',
        'partner_id',
        string='Membresías de Biblioteca'
    )

    # Indicador de si es miembro de biblioteca
    is_library_member = fields.Boolean(
        string='Es Miembro de Biblioteca',
        compute='_compute_is_library_member',
        help='Indica si este contacto tiene una membresía de biblioteca'
    )

    # Membresía activa (si existe)
    active_library_member_id = fields.Many2one(
        'library.member',
        string='Membresía Activa',
        compute='_compute_active_library_member',
        help='Membresía de biblioteca activa de este contacto'
    )

    # =========================================================================
    # MÉTODOS COMPUTADOS
    # =========================================================================

    @api.depends('library_member_ids')
    def _compute_is_library_member(self):
        """
        Verifica si el contacto es miembro de biblioteca.
        """
        for partner in self:
            partner.is_library_member = bool(partner.library_member_ids)

    @api.depends('library_member_ids', 'library_member_ids.state')
    def _compute_active_library_member(self):
        """
        Obtiene la membresía activa del contacto.

        Prioriza membresías con estado 'active'.
        """
        for partner in self:
            active_member = partner.library_member_ids.filtered(
                lambda m: m.state == 'active'
            )
            partner.active_library_member_id = active_member[:1] if active_member else False
