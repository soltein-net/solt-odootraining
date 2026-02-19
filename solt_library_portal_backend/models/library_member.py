# -*- coding: utf-8 -*-
"""
================================================================================
EXTENSIÓN DEL MODELO MEMBER PARA EL PORTAL
================================================================================

Este archivo extiende el modelo library.member para agregar funcionalidades
de acceso al portal.

CONCEPTOS CLAVE PARA LA CAPACITACIÓN:
-------------------------------------

1. ACCESO AL PORTAL:
   - Los miembros de biblioteca pueden ver sus datos en el portal
   - Necesitan permisos específicos para acceder

2. CAMPOS RELACIONADOS CON res.users:
   - Un miembro puede tener un usuario asociado
   - El usuario permite acceso al portal
"""

from odoo import api, fields, models


class LibraryMember(models.Model):
    _inherit = 'library.member'

    # =========================================================================
    # CAMPOS PARA ACCESO AL PORTAL
    # =========================================================================

    # Indica si el miembro tiene acceso al portal
    portal_access = fields.Boolean(
        string='Acceso al Portal',
        compute='_compute_portal_access',
        help='Indica si el miembro puede acceder al portal web'
    )

    # Usuario del portal asociado (si existe)
    portal_user_id = fields.Many2one(
        'res.users',
        string='Usuario del Portal',
        compute='_compute_portal_user',
        help='Usuario del portal asociado a este miembro'
    )

    # =========================================================================
    # MÉTODOS COMPUTADOS
    # =========================================================================

    @api.depends('partner_id', 'partner_id.user_ids')
    def _compute_portal_access(self):
        """
        Verifica si el miembro tiene acceso al portal.

        Un miembro tiene acceso si:
        1. Tiene un partner asociado
        2. El partner tiene un usuario
        3. El usuario tiene el grupo de portal
        """
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)

        for member in self:
            has_access = False
            if member.partner_id and portal_group:
                # Buscar usuarios del partner con grupo portal
                portal_users = member.partner_id.user_ids.filtered(
                    lambda u: portal_group in u.groups_id
                )
                has_access = bool(portal_users)
            member.portal_access = has_access

    @api.depends('partner_id', 'partner_id.user_ids')
    def _compute_portal_user(self):
        """
        Obtiene el usuario del portal asociado al miembro.
        """
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)

        for member in self:
            user = False
            if member.partner_id and portal_group:
                portal_users = member.partner_id.user_ids.filtered(
                    lambda u: portal_group in u.groups_id
                )
                if portal_users:
                    user = portal_users[0]
            member.portal_user_id = user

    # =========================================================================
    # MÉTODOS AUXILIARES PARA EL PORTAL
    # =========================================================================

    def get_portal_url(self):
        """
        Retorna la URL del perfil en el portal.

        Returns:
            str: URL del perfil del miembro
        """
        self.ensure_one()
        return '/my/library/profile'

    def get_membership_badge_class(self):
        """
        Retorna la clase CSS para el badge de membresía.

        Returns:
            str: Clase CSS para el tipo de membresía
        """
        self.ensure_one()
        badge_classes = {
            'student': 'info',
            'regular': 'primary',
            'premium': 'warning',
            'lifetime': 'success',
        }
        return badge_classes.get(self.membership_type, 'secondary')

    def get_state_badge_class(self):
        """
        Retorna la clase CSS para el badge de estado.

        Returns:
            str: Clase CSS para el estado del miembro
        """
        self.ensure_one()
        badge_classes = {
            'active': 'success',
            'suspended': 'warning',
            'expired': 'danger',
        }
        return badge_classes.get(self.state, 'secondary')

    def get_remaining_loans(self):
        """
        Calcula cuántos préstamos adicionales puede hacer el miembro.

        Returns:
            int: Número de préstamos disponibles
        """
        self.ensure_one()
        return max(0, self.max_loans - self.active_loan_count)

    def can_borrow(self):
        """
        Verifica si el miembro puede pedir prestado un libro.

        Returns:
            tuple: (bool, str) - (puede_pedir, razón)
        """
        self.ensure_one()

        if self.state != 'active':
            return False, 'Tu membresía no está activa'

        if self.active_loan_count >= self.max_loans:
            return False, 'Has alcanzado el límite de préstamos'

        if self.pending_fees > 0:
            return False, 'Tienes recargos pendientes por pagar'

        return True, 'Puedes pedir prestado'

    @api.model
    def get_member_for_user(self, user=None):
        """
        Obtiene el miembro de biblioteca para un usuario.

        Función útil para controladores que necesitan obtener
        el miembro asociado al usuario actual.

        Args:
            user: Usuario (por defecto el usuario actual)

        Returns:
            recordset: Miembro de biblioteca o recordset vacío
        """
        if user is None:
            user = self.env.user

        return self.sudo().search([
            ('partner_id', '=', user.partner_id.id)
        ], limit=1)
