import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LibraryMembersController(http.Controller):
    @http.route(["/registro"], auth='public', type='http', website=True)
    def members_register(self):
        if not request.env.user._is_public():
            return request.redirect("/")
        if request.httprequest.method == 'POST':
            email = request.params.get('user-email')
            password = request.params.get('user-password')
            member_type = request.params.get('user-member-type')
            if email and password:
                try:
                    existing_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
                    if existing_user:
                        return request.render('website_solt_library.members_register', {
                            'error': 'El correo ya está registrado.'
                        })
                    new_user = request.env['res.users'].sudo().create({
                        'name': email.split('@')[0],
                        'login': email,
                        'password': password,
                        'share': False,
                        'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])]
                    })
                    if new_user:
                        request.env["library.member"].sudo().create({
                            'partner_id': new_user.partner_id.id,
                            'code': new_user.login.upper().replace('@', '_').replace('.', '_'),
                            'membership_type': member_type,
                        })
                    return request.redirect('/')
                except Exception as e:
                    _logger.exception(f"Error creando usuario: {str(e)}")
                    return request.render('website_solt_library.members_register', {
                        'error': 'Error al crear la cuenta. Contacte con los administradores.'
                    })
            else:
                return request.render('website_solt_library.members_register', {
                    'error': 'Por favor, completa todos los campos.'
                })
        return request.render('website_solt_library.members_register', {})