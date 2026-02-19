from ast import literal_eval
from odoo import http
from odoo.addons.website.controllers.main import QueryURL
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.addons.website_profile.controllers.main import WebsiteProfile
from odoo.addons.portal.controllers.portal import pager as portal_pager


class LibraryBooksController(WebsiteProfile):
    _BOOKS_PER_PAGE = 10
    _BOOK_ORDER_BY_CRITERION = {
        'date': 'publication_date desc',
        'name': 'name desc',
    }

    def _get_book_search_options(self, author_tags=None, category=None, **post):
        return {
            'displayDescription': True,
            'displayDetail': False,
            'displayExtraDetail': False,
            'displayExtraLink': False,
            'displayImage': False,
            'allowFuzzy': not post.get('noFuzzy'),
            'author': author_tags or post.get('author'),
            'category': category,
        }

    def _slugify_tags(self, tag_ids, toggle_tag_id=None):
        tag_ids = list(tag_ids)  # required to avoid using the same list
        if toggle_tag_id and toggle_tag_id in tag_ids:
            tag_ids.remove(toggle_tag_id)
        elif toggle_tag_id:
            tag_ids.append(toggle_tag_id)
        return ','.join(slug(tag) for tag in request.env['library.author'].browse(tag_ids))

    def _book_search_tags_ids(self, search_tags):
        """ Input: %5B4%5D """
        author_model = request.env['library.author']
        try:
            tag_ids = literal_eval(search_tags or '')
        except Exception:
            return author_model
        # perform a search to filter on existing / valid tags implicitly
        return author_model.search([('id', 'in', tag_ids)]) if tag_ids else author_model

    def _book_search_tags_slug(self, search_tags):
        """ Input: shakespeare-1,molliere-2 """
        author_model = request.env['library.author']
        try:
            author_ids = list(filter(None, [unslug(tag)[1] for tag in (search_tags or '').split(',')]))
        except Exception:
            return author_model
        # perform a search to filter on existing / valid tags implicitly
        return author_model.search([('id', 'in', author_ids)]) if author_ids else author_model

    def _book_render_context_base(self):
        return {
            # current user info
            'user': request.env.user,
            'is_public_user': request.website.is_public_user(),
            # tools
            '_slugify_tags': self._slugify_tags,
        }

    def slides_channel_all_values(self, category=None, author_tags=None, **post):
        options = self._get_book_search_options(
            author_tags=author_tags,
            category=category,
            **post
        )
        search = post.get('search')
        sorting_criterion = post.get('sorting', 'date')
        order = self._BOOK_ORDER_BY_CRITERION.get(sorting_criterion, 'publication_date desc')
        page = post.get('page', 1)
        offset = (page - 1) * self._BOOKS_PER_PAGE
        search_count, details, fuzzy_search_term = request.website._search_with_fuzzy(
            "books_only", search, limit=1000, order=order, options=options
        )
        books = details[0].get('results', request.env['library.book'])[offset:offset + self._BOOKS_PER_PAGE]
        
        if author_tags:
            search_tags = self._book_search_tags_slug(author_tags)
        elif post.get('tags'):
            search_tags = self._book_search_tags_ids(post['tags'])
        else:
            search_tags = request.env['library.author']
        pager = portal_pager(
            url="/libros",
            url_args={'author': self._slugify_tags(search_tags.ids), 'search': fuzzy_search_term or search, 'category': category},
            total=search_count,
            page=page,
            step=self._BOOKS_PER_PAGE
        )
        render_values = self._book_render_context_base()
        render_values.update(self._prepare_user_values(**post))
        render_values.update({
            'books': books,
            'search_term': fuzzy_search_term or search,
            'original_search': fuzzy_search_term and search,
            'search_category': category,
            'search_tags': search_tags,
            'search_count': search_count,
            'slugify_tags': self._slugify_tags,
            'book_query_url': QueryURL('/libros', ['author']),
            'authors': request.env['library.author'].search([]),
            'categories': request.env['library.category'].search([]),
            'category': request.env['library.category'].browse(int(category)) if category else None,
            'pager': pager,
        })

        return render_values

    @http.route([
        "/libros",
        "/libros/page/<int:page>",
        "/libros/author/<string:author_tags>",
        "/libros/author/<string:author_tags>/page/<int:page>"
    ], auth='public', type='http', website=True)
    def list_books(self, page=1, author_tags=None, category=None, **post):
        if author_tags and request.httprequest.method == 'GET':
            # Redirect `author-1,author-2` to `author-1` to disallow multi authors
            # in GET request for proper bot indexation;
            # if the search term is available, do not remove any existing
            # authors because it is user who provided search term with GET
            # request and so clearly it's not SEO bot.
            author_list = author_tags.split(',')
            if len(author_list) > 1 and not post.get('search'):
                url = QueryURL('/libros', ['author'], author=author_list[0], category=category)()
                return request.redirect(url, code=302)

        render_values = self.slides_channel_all_values(category=category, author_tags=author_tags, page=page, **post)
        return request.render('website_solt_library.books_list', render_values)

    @http.route(["/libros/<int:book_id>"], auth='public', type='http', website=True)
    def book_detail(self, book_id, **kwargs):
        book = request.env['library.book'].search([
            ('id', '=', book_id),
            ('website_published', '=', True),
        ], limit=1)
        if not book:
            return request.redirect('/libros')
        render_values = self._book_render_context_base()
        render_values.update(self._prepare_user_values(**kwargs))
        render_values['book'] = book
        return request.render('website_solt_library.book_detail', render_values)

    @http.route(["/libros/loan/<int:book_id>"], auth='user', type='http', website=True)
    def books_create_loan(self, book_id, **kwargs):
        member = request.env['library.member'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)], limit=1)
        render_values = self.slides_channel_all_values(**kwargs)
        if not member:
            return request.render('website_solt_library.books_list', {
                **render_values,
                'error': 'No eres un miembro registrado. Por favor, contacta a la biblioteca.',
            })
        book = request.env['library.book'].search([('id', '=', book_id)], limit=1)
        if not book:
            return request.render('website_solt_library.books_list', {
                **render_values,
                'error': 'El libro no existe.',
            })
        if book.available_qty <= 0:
            return request.render('website_solt_library.books_list', {
                **render_values,
                'error': 'Lo sentimos, este libro no está disponible en este momento.',
            })
        loans = request.env['library.loan'].search([
            ('member_id', '=', member.id), ('book_id', '=', book.id), ('state', '=', 'loaned')
        ], limit=1)
        if loans and len(loans) >= 0:
            return request.render('website_solt_library.books_list', {
                **render_values,
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
                **render_values,
                'error': 'Hubo un error al crear el préstamo. Por favor, inténtalo de nuevo.',
            })
        return request.render('website_solt_library.books_list', {
            **render_values,
            'success': 'El préstamo se ha creado correctamente.',
        })
