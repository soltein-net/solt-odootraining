from odoo import api, models
from odoo.addons.http_routing.models.ir_http import unslug


class LibraryBook(models.Model):
    _name = 'library.book'
    _inherit = ['library.book', 'website.published.multi.mixin', 'website.searchable.mixin']

    @api.depends_context('lang')
    def _compute_website_url(self):
        for record in self:
            record.website_url = f'/libros/{record.id}'

    @api.model
    def _search_get_detail(self, website, order, options):
        with_description = options['displayDescription']
        with_date = options['displayDetail']
        author_tags = options.get('author')
        category = options.get('category')
        try:
            category = int(category) if category else 0
        except ValueError:
            category = 0
        domain = [website.website_domain()]
        if author_tags:
            author_model = self.env['library.author']
            try:
                tag_ids = list(filter(None, [unslug(tag)[1] for tag in author_tags.split(',')]))
                authors = author_model.search([('id', 'in', tag_ids)]) if tag_ids else author_model
            except Exception:
                authors = author_model
            domain.append([('author_ids', 'in', authors.ids)])
        if category:
            domain.append([('category_id', '=', category)])
        search_fields = ['name']
        fetch_fields = ['name', 'website_url']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'website_url': {'name': 'website_url', 'type': 'text', 'truncate': False},
        }
        if with_description:
            search_fields.append('description')
            fetch_fields.append('description')
            mapping['description'] = {'name': 'description', 'type': 'text', 'match': True}
        if with_date:
            fetch_fields.append('publication_date')
            mapping['detail'] = {'name': 'publication_date', 'type': 'date'}
        return {
            'model': 'library.book',
            'base_domain': domain,
            'search_fields': search_fields,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-book',
        }

    def has_active_loan_for_partner(self, partner_id=None):
        """
        Check if a partner has an active loan of this book.

        :param partner_id: ID of the partner to check. If None, uses current user's partner.
        :return: True if partner has an active loan of this book, False otherwise.
        """
        self.ensure_one()
        if partner_id is None:
            partner_id = self.env.user.partner_id.id

        member = self.env['library.member'].search([
            ('partner_id', '=', partner_id)
        ], limit=1)

        if not member:
            return False

        active_loan = self.env['library.loan'].search([
            ('book_id', '=', self.id),
            ('member_id', '=', member.id),
            ('state', '=', 'loaned')
        ], limit=1)

        return bool(active_loan)