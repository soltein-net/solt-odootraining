from odoo import http
from odoo.http import request


class LibraryLoansController(http.Controller):
    @http.route(["/prestamos/create/<int:book_id>"], auth='user', type='http', website=True)
    def create_loan(self, book_id, **kwargs):
        member = request.env['library.member'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)], limit=1)
        if not member:
            return request.render('website_solt_library.books_list', {
                'error': 'No eres un miembro registrado. Por favor, contacta a la biblioteca.',
            })
        book = request.env['library.book'].search([('id', '=', book_id)], limit=1)
        if not book:
            return request.render('website_solt_library.books_list', {
                'error': 'El libro no existe.',
            })
        if book.available_qty <= 0:
            return request.render('website_solt_library.books_list', {
                'error': 'Lo sentimos, este libro no está disponible en este momento.',
            })
        loans = request.env['library.loan'].search([('member_id', '=', member.id), ('state', '=', 'loaned')], limit=1)
        if loans and len(loans) >= 0:
            return request.render('website_solt_library.books_list', {
                'error': 'Ya ha solicitado un prestamo de este libro.',
            })
        loan = request.env['library.loan'].create({
            'member_id': member.id,
            'book_id': book.id,
            'reference': f'Loan-{member.id}-{book.id}',
            'state': 'loaned'
        })
        if not loan:
            return request.render('website_solt_library.books_list', {
                'error': 'Hubo un error al crear el préstamo. Por favor, inténtalo de nuevo.',
            })
        return request.render('website_solt_library.books_list', {
            'success': 'El préstamo se ha creado correctamente.',
        })
        
        