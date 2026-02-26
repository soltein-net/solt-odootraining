from odoo import http
from odoo.http import request
from odoo.addons.website_profile.controllers.main import WebsiteProfile
from odoo.addons.portal.controllers.portal import pager as portal_pager


class LibraryAuthorsController(WebsiteProfile):
    _AUTHORS_PER_PAGE = 12
    _AUTHOR_ORDER_BY_CRITERION = {
        'name': 'name',
        'books': 'book_count desc',
    }

    def _author_render_context_base(self):
        return {
            'user': request.env.user,
            'is_public_user': request.website.is_public_user(),
        }

    @http.route([
        "/autores",
        "/autores/page/<int:page>",
    ], auth='public', type='http', website=True)
    def list_authors(self, page=1, search=None, sorting=None, **kwargs):
        """List all authors with pagination and search"""
        author_model = request.env['library.author']
        
        # Build domain
        domain = []
        if search:
            domain = ['|', ('name', 'ilike', search), ('nationality', 'ilike', search)]
        
        # Get order
        order = self._AUTHOR_ORDER_BY_CRITERION.get(sorting or 'name', 'name')
        
        # Count total
        author_count = author_model.search_count(domain)
        
        # Setup pager
        pager = portal_pager(
            url="/autores",
            url_args={'search': search, 'sorting': sorting},
            total=author_count,
            page=page,
            step=self._AUTHORS_PER_PAGE
        )
        
        # Get authors for current page
        authors = author_model.search(
            domain,
            order=order,
            limit=self._AUTHORS_PER_PAGE,
            offset=pager['offset']
        )
        
        # Prepare render values
        render_values = self._author_render_context_base()
        render_values.update(self._prepare_user_values(**kwargs))
        render_values.update({
            'authors': authors,
            'search_term': search,
            'sorting': sorting or 'name',
            'pager': pager,
            'author_count': author_count,
        })
        
        return request.render('website_solt_library.authors_list', render_values)

    @http.route(["/autores/<int:author_id>"], auth='public', type='http', website=True)
    def author_detail(self, author_id, **kwargs):
        """Display author detail page"""
        author = request.env['library.author'].search([
            ('id', '=', author_id),
        ], limit=1)
        
        if not author:
            return request.redirect('/autores')
        
        # Get author's books with published filter if applicable
        books = author.book_ids
        if hasattr(books, 'filtered'):
            # Filter published books for public users
            if request.website.is_public_user():
                books = books.filtered(lambda b: hasattr(b, 'website_published') and b.website_published)
        
        # Prepare render values
        render_values = self._author_render_context_base()
        render_values.update(self._prepare_user_values(**kwargs))
        render_values.update({
            'author': author,
            'books': books,
            'book_count': len(books),
        })
        
        return request.render('website_solt_library.author_detail', render_values)
