import logging
from operator import itemgetter
from typing import Any

from odoo import _, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.website_common.controllers.portal import CommonPortalController
from odoo.addons.website_common.utils.search import (
    DEFAULT_FILTERBY,
    DEFAULT_SORTBY,
    change_previous_next_record_url,
    model_instance_stage_name,
)
from odoo.addons.website_common.utils.urls import get_url
from odoo.addons.website_solt_profile.utils.http import check_employee_or_redirect
from odoo.addons.website_solt_profile.utils.website import set_flash_message
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.osv.expression import AND, OR
from odoo.tools import groupby as groupbyelem
from werkzeug.wrappers.response import Response

_logger = logging.getLogger(__name__)


class LoansPortal(CustomerPortal):
    """Portal controller for maintenance request management."""

    # Constants
    _DEFAULT_ITEMS_PER_PAGE = 80
    _MAX_HISTORY_ITEMS = 100  # Maximum number of maintenance request IDs to store in session history
    _HISTORY_SESSION_KEY = "my_loans_history"
    _BASE_URL = "/my/loans"
    _MODEL_NAME = "library.loan"
    _TEMPLATE_LIST = "website_solt_library.portal_my_loans"
    _TEMPLATE_DETAIL = "website_solt_library.portal_my_loan"
    _PAGE_NAME_LIST = "all_loans"
    _PAGE_NAME_DETAIL = "loan"

    # Groupable field types - used to validate groupby parameter
    _GROUPABLE_FIELD_TYPES = frozenset(['many2one', 'selection', 'char', 'integer', 'date', 'datetime', 'boolean'])

    def _get_loan_domain(self, domain: list | None = None) -> list:
        if domain is None:
            domain = []

        user = request.env.user
        domain = AND([domain, [("member_id.partner_id", "=", user.partner_id.id)]])

        return domain

    @staticmethod
    def _get_searchbar_listings() -> dict[int, dict[str, Any]]:
        """
        Return available listing options (items per page) for the searchbar.

        Returns:
            dict: Dictionary where keys are item counts and values contain:
                - input (str): String representation of the count
                - label (str): Translatable display label
                - order (int): Sort order value
        """
        values = {
            10: {"input": "10", "label": _("10 elements"), "order": 10},
            20: {"input": "20", "label": _("20 elements"), "order": 20},
            40: {"input": "40", "label": _("40 elements"), "order": 40},
            80: {"input": "80", "label": _("80 elements"), "order": 80},
            160: {"input": "160", "label": _("160 elements"), "order": 160},
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _validate_view_data(self, view_data: dict) -> None:
        """
        Validate that view_data contains all required keys.

        Args:
            view_data (dict): The view data dictionary to validate.

        Raises:
            ValidationError: If required keys are missing from view_data.
        """
        # Only group_by_mapping and inputs are truly required
        # Other keys like inputs_mapping, filters, date_filters are optional
        required_keys = ["group_by_mapping", "inputs", "group_by"]
        missing_keys = [key for key in required_keys if key not in view_data]

        if missing_keys:
            raise ValidationError(
                _("View data is missing required keys: %s") % ", ".join(missing_keys)
            )

    def _get_searchbar_filters(self, view_data: dict) -> dict[str, dict]:
        """
        Build searchbar filters for maintenance requests.

        Constructs a comprehensive filter dictionary that includes:
        - A default 'all' filter with an empty domain
        - Date-based filters from view_data configuration
        - Additional custom filters from view_data

        Args:
            view_data (dict): Dictionary containing filter configurations.

        Returns:
            dict[str, dict]: Dictionary where each key is a filter identifier and
                each value is a filter configuration dict containing:
                - label (str): Localized filter display name
                - domain (list): Filter domain for database queries
                - sequence (int): Display order of the filter

        Raises:
            ValidationError: If view_data doesn't contain required filter keys.
        """
        searchbar_filters = {
            "all": {"label": _("All"), "domain": [], "sequence": 1},
        }

        try:
            # view_data["filters"] is a tuple returned by FilterBarParser._parse_filters()
            # which returns (filters_dict, date_filters_dict)
            filters_tuple = view_data.get("filters", ({}, {}))
            if not isinstance(filters_tuple, tuple) or len(filters_tuple) != 2:
                _logger.error(
                    "Expected filters to be a tuple of 2 elements, got: %s (type: %s)",
                    filters_tuple,
                    type(filters_tuple)
                )
                filters, date_filters = {}, {}
            else:
                filters, date_filters = filters_tuple
        except (KeyError, ValueError) as e:
            _logger.error("Invalid filter configuration in view_data: %s", e)
            raise ValidationError(_("Invalid filter configuration")) from e

        # Add date-based filters
        for date_filter in date_filters.values():
            searchbar_filters.update(
                CommonPortalController.add_date_searchbar_filters(
                    date_filter["name"],
                    date_filter["label"],
                    date_filter["sequence"],
                    request.env.context.get("lang", "en_US"),
                )
            )

        # Add custom filters
        searchbar_filters.update(filters)

        return searchbar_filters

    def _get_search_domain(self, view_data: dict, search_in: str, search: str) -> list:
        """
        Build a search domain based on search input and field mapping.

        Constructs an OR-combined search domain by iterating through the configured
        input mappings and matching the search criteria against the specified fields.

        Args:
            view_data (dict): Dictionary containing inputs_mapping configuration.
            search_in (str): The search category/option to match.
            search (str): The search term to filter by.

        Returns:
            list: An Odoo domain expression using OR logic. Returns empty list if
                no matching search options are found or inputs_mapping is missing.

        Raises:
            ValidationError: If view_data doesn't contain inputs_mapping.
        """
        inputs_mapping = view_data.get("inputs_mapping", {})

        if not inputs_mapping:
            _logger.warning("inputs_mapping not found in view_data, returning empty search domain")
            return []

        search_domain = []
        for search_in_option, search_field in inputs_mapping.items():
            if search_in in search_in_option:
                field_domain = (
                    [(search_field, "ilike", search)]
                    if isinstance(search_field, str)
                    else search_field
                )
                search_domain = OR([search_domain, field_domain])

        return search_domain

    def _prepare_home_portal_values(self, counters: dict) -> dict:
        """
        Prepare values for the home portal view.

        Adds the maintenance requests count to the portal home view if requested.

        Args:
            counters (dict): Dictionary containing various counters for the portal.

        Returns:
            dict: Updated values dictionary including maintenance_requests_count
                if present in counters.
        """
        values = super()._prepare_home_portal_values(counters)

        if "loans_count" in counters and request.env:
            domain = self._get_loan_domain()
            values["loans_count"] = (
                request.env[self._MODEL_NAME]
                .with_context(active_test=False)
                .search_count(domain)
            )

        return values

    def _get_maintenance_request_page_values(self, loan, **kwargs) -> dict:
        """
        Prepare view values for the maintenance request detail page.

        Constructs a dictionary of values used to render the maintenance request page,
        including the request object, current user, and page metadata.

        Args:
            maintenance_request: The maintenance request recordset to display.
            **kwargs: Additional keyword arguments including:
                - tab (str, optional): Active tab name. Defaults to 'information'.
                - access_token (str, optional): Access token for validation.
                - Other arguments passed to _get_page_view_values().

        Returns:
            dict: Dictionary containing page values including:
                - page_name (str): Page identifier
                - maintenance_request: The maintenance request object
                - user: Current authenticated user
                - preview_object: The request object for preview
                - tab (str): Active tab name
                - prev_record/next_record: Navigation URLs
        """
        values = {
            "page_name": self._PAGE_NAME_DETAIL,
            "maintenance_request": loan,
            "user": request.env.user,
            "preview_object": loan,
            "tab": kwargs.get("tab", "information"),
        }

        values = self._get_page_view_values(
            loan,
            kwargs.get("access_token", None),
            values,
            self._HISTORY_SESSION_KEY,
            False,
            **kwargs,
        )

        return values

    def _setup_search_configuration(self, search: str | None = None) -> dict:
        """
        Set up search configuration by extracting search view metadata.

        Args:
            search (str | None): Optional search term.

        Returns:
            dict: View data containing searchbar configuration.
        """
        view_data = CommonPortalController.extract_search_view_to_searchbar(
            self._MODEL_NAME,
            include_fields_on_search_panel=True,
            include_first_level_filters_only=True,
            search=search,
        )

        # Validate the extracted view data
        self._validate_view_data(view_data)

        return view_data

    def _prepare_searchbar_options(self, view_data: dict) -> tuple[dict, dict, dict]:
        """
        Prepare searchbar options for sorting, inputs, and grouping.

        Args:
            view_data (dict): Dictionary containing view configuration.

        Returns:
            tuple: (searchbar_sortings, searchbar_inputs, searchbar_groupby)
        """
        searchbar_sortings = {
            "reference_asc": {"label": _("Reference Asc"), "order": "reference asc, id"},
            "reference_desc": {"label": _("Reference Desc"), "order": "reference desc, id"},
        }

        searchbar_inputs = {
            "all": {"label": _("Search in All"), "input": "all"},
        }
        searchbar_inputs.update(view_data["inputs"])

        searchbar_groupby = {
            "none": {"label": _("None"), "input": "none"},
        }
        searchbar_groupby.update(view_data["group_by"])

        return searchbar_sortings, searchbar_inputs, searchbar_groupby

    def _build_domain(
        self,
        view_data: dict,
        filterby: str,
        searchbar_filters: dict,
        search: str | None,
        search_in: str,
    ) -> list:
        """
        Build the complete domain for maintenance request search.

        Args:
            view_data (dict): View configuration data.
            filterby (str): Filter key to apply.
            searchbar_filters (dict): Available filter options.
            search (str | None): Search term.
            search_in (str): Field to search in.

        Returns:
            list: Complete domain for the search query.
        """
        domain = self._get_loan_domain()

        # Apply filter
        filter_data = searchbar_filters.get(filterby, searchbar_filters["all"])
        if filter_data and "domain" in filter_data:
            domain = AND([domain, filter_data["domain"]])

        # Apply search
        if search and search_in:
            search_domain = self._get_search_domain(view_data, search_in, search)
            domain = AND([domain, search_domain])

        return domain

    def _get_grouped_records(
        self,
        records,
        groupby_field: str | None,
        maintenance_request_object,
    ) -> list:
        """
        Group maintenance request records by specified field.

        This method efficiently groups records by a specified field, with special
        handling for Many2one fields to prevent N+1 queries. For Many2one fields,
        it ensures the related records are prefetched before grouping.

        Args:
            records: Maintenance request recordset.
            groupby_field (str | None): Field name to group by.
            maintenance_request_object: Model object for concatenation.

        Returns:
            list: List of grouped recordsets.

        Performance:
            - For Many2one fields: Prefetches related records to avoid N+1 queries
            - For other field types: Direct grouping using itemgetter
        """
        if not groupby_field:
            return [records] if records else []

        if not records:
            return []

        # Check if groupby_field is a Many2one to optimize prefetching
        field_obj = maintenance_request_object._fields.get(groupby_field)
        if field_obj and field_obj.type == "many2one":
            # Prefetch the Many2one field to avoid N+1 queries
            # This loads all related records in a single query
            records.mapped(groupby_field)

        # Group records by the specified field
        grouped = [
            maintenance_request_object.concat(*g)
            for _, g in groupbyelem(records, itemgetter(groupby_field))
        ]

        return grouped

    def _maintenance_request_entries_display(
        self,
        page: int = 1,
        date_begin: str | None = None,
        date_end: str | None = None,
        sortby: str | None = None,
        filterby: str | None = None,
        search: str | None = None,
        search_in: str = "all",
        groupby: str | None = None,
        listing: int = 80,
        template: str | None = None,
        query_with_sudo: bool = False,
        **kw,
    ) -> http.Response:
        """
        Render the portal maintenance requests list page.

        This method handles the main list view with comprehensive support for:
        - Filtering by status, dates, and custom criteria
        - Sorting by various fields
        - Grouping by configurable fields
        - Searching across multiple fields
        - Pagination with configurable items per page

        Args:
            page (int): Current page number for pagination. Defaults to 1.
            date_begin (str | None): Start date filter (ISO format).
            date_end (str | None): End date filter (ISO format).
            sortby (str | None): Sorting key from searchbar_sortings.
            filterby (str | None): Filter key from searchbar_filters.
            search (str | None): Search query string.
            search_in (str): Field category to search in. Defaults to "all".
            groupby (str | None): Grouping key from searchbar_groupby.
            listing (int): Number of items per page. Defaults to 80.
            template (str | None): QWeb template to render. Uses default if None.
            query_with_sudo (bool): Whether to bypass access rules. Defaults to False.
            **kw: Additional keyword arguments (layout, tab, etc.).

        Returns:
            http.Response: Rendered portal page with maintenance requests.

        Raises:
            ValidationError: If groupby field doesn't exist in the model.
        """
        # Use default template if none specified
        if template is None:
            template = self._TEMPLATE_LIST

        # Initialize values
        values = self._prepare_portal_layout_values()
        if not request.env:
            raise AccessError(_("No environment available in request context"))
        maintenance_request_object = (
            request.env[self._MODEL_NAME].sudo()
            if query_with_sudo
            else request.env[self._MODEL_NAME]
        )

        # Setup search configuration
        view_data = self._setup_search_configuration(search)

        # Prepare searchbar options
        searchbar_sortings, searchbar_inputs, searchbar_groupby = (
            self._prepare_searchbar_options(view_data)
        )

        # Get listing options and validate items per page
        listings = self._get_searchbar_listings()
        try:
            listing = int(listing)
        except (ValueError, TypeError):
            _logger.warning("Invalid listing value: %s, using default", listing)
            listing = self._DEFAULT_ITEMS_PER_PAGE

        items_per_page = listing if listing in listings else self._DEFAULT_ITEMS_PER_PAGE

        # Get layout and tab
        layout = kw.get("layout", "list")
        tab = kw.get("tab", "maintenance_requests")

        # Setup sorting - validate sortby against whitelist to prevent SQL injection
        if sortby and sortby not in searchbar_sortings:
            _logger.warning(
                "Invalid sortby parameter '%s' from user %s. Using default.",
                sortby,
                request.env.user.login,
            )
            sortby = 'reference_asc'
        elif not sortby:
            sortby = 'reference_asc'

        sort_order = searchbar_sortings[sortby]["order"]

        # Setup grouping
        groupby_mapping = view_data["group_by_mapping"]
        groupby_field = groupby_mapping.get(groupby)

        # Validate groupby field if specified
        if groupby_field:
            group_by_field = maintenance_request_object._fields.get(groupby_field)
            if not group_by_field:
                raise ValidationError(
                    _("The field '%s' does not exist in the model.", groupby_field)
                )
            groupby_type = group_by_field.type

            # Validate field type is groupable
            if groupby_type not in self._GROUPABLE_FIELD_TYPES:
                _logger.warning(
                    "Invalid groupby field type '%s' for field '%s' from user %s.",
                    groupby_type,
                    groupby_field,
                    request.env.user.login,
                )
                raise ValidationError(
                    _("The field '%s' of type '%s' cannot be used for grouping.", groupby_field, groupby_type)
                )
        else:
            group_by_field = None
            groupby_type = "char"

        # Build order clause
        order = f"{groupby_field}, {sort_order}" if groupby_field else sort_order

        # Setup filtering
        searchbar_filters = self._get_searchbar_filters(view_data)
        filterby = filterby or DEFAULT_FILTERBY

        # Build domain
        domain = self._build_domain(
            view_data, filterby, searchbar_filters, search, search_in
        )

        # Count records and setup pagination
        maintenance_requests_count = maintenance_request_object.search_count(domain)
        pager = portal_pager(
            url=self._BASE_URL,
            url_args={
                "sortby": sortby,
                "search_in": search_in,
                "search": search,
                "groupby": groupby,
                "filterby": filterby,
                "listing": listing,
                "layout": layout,
            },
            total=maintenance_requests_count,
            page=page,
            step=items_per_page,
        )

        # Fetch records
        maintenance_requests = maintenance_request_object.search(
            domain, order=order, limit=items_per_page, offset=pager["offset"]
        )

        # Update session history with limited IDs to prevent session bloat
        request.session[self._HISTORY_SESSION_KEY] = maintenance_requests.ids[:self._MAX_HISTORY_ITEMS]

        # Group records if needed
        grouped_maintenance_requests = self._get_grouped_records(
            maintenance_requests, groupby_field, maintenance_request_object
        )

        # Helper function to preserve URL parameters
        def keep_the_url(**kwargs: dict) -> str:
            """
            Build a URL preserving current page and filter parameters.

            Args:
                **kwargs: Parameters to override or add to the URL.

            Returns:
                str: The constructed URL with query parameters.
            """
            url = kwargs.get("url", self._BASE_URL)
            if not isinstance(url, str):
                url = self._BASE_URL

            return get_url(
                url,
                page,
                {
                    "date_begin": date_begin,
                    "date_end": date_end,
                    "sortby": sortby,
                    "search": search,
                    "search_in": search_in,
                    "groupby": groupby,
                    "listing": listing,
                    "layout": layout,
                }
                | kwargs,
            )

        # Update values with all required data
        values.update(
            {
                "maintenance_requests": maintenance_requests,
                "grouped_maintenance_requests": grouped_maintenance_requests,
                "page_name": self._PAGE_NAME_LIST,
                "pager": pager,
                "default_url": self._BASE_URL,
                "groupby_mapping": groupby_mapping,
                "searchbar_sortings": searchbar_sortings,
                "search_in": search_in,
                "search": search,
                "sortby": sortby,
                "groupby": groupby or "none",
                "groupby_type": groupby_type,
                "filterby": filterby,
                "searchbar_inputs": searchbar_inputs,
                "searchbar_groupby": searchbar_groupby,
                "searchbar_filters": searchbar_filters,
                "layout": layout,
                "maintenance_requests_count": maintenance_requests_count,
                "listing": listing,
                "searchbar_listings": listings,
                "keep_the_url": keep_the_url,
                "type": type,
                "additional_title": _("Loans"),
                "tab": tab,
                "stage_name": model_instance_stage_name,
            }
        )

        return request.render(template, values)

    @http.route(
        ["/my/loans", "/my/loans/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def my_maintenance_requests(
        self,
        page: int = 1,
        date_begin: str | None = None,
        date_end: str | None = None,
        sortby: str | None = None,
        filterby: str | None = None,
        search: str | None = None,
        search_in: str = "all",
        groupby: str | None = None,
        listing: int = 80,
        **kw,
    ) -> http.Response:
        """
        Display maintenance requests for the current user.

        Public route that shows a paginated list of maintenance requests accessible
        to the current user. Supports comprehensive filtering, searching, sorting,
        and grouping capabilities.

        Security:
            - Portal users: Can only see their own maintenance requests
            - Internal users: See requests based on access rights and record rules

        Args:
            page (int): Page number for pagination. Defaults to 1.
            date_begin (str | None): Start date filter (ISO format).
            date_end (str | None): End date filter (ISO format).
            sortby (str | None): Field to sort results by.
            filterby (str | None): Filter criteria to apply.
            search (str | None): Search query string.
            search_in (str): Scope of search ("all" or specific field).
            groupby (str | None): Field to group results by.
            listing (int): Items to display per page. Defaults to 80.
            **kw: Additional keyword arguments (layout, tab, etc.).

        Returns:
            http.Response: Rendered maintenance requests list page.
        """
        return self._maintenance_request_entries_display(
            page=page,
            date_begin=date_begin,
            date_end=date_end,
            sortby=sortby,
            filterby=filterby,
            search=search,
            search_in=search_in,
            groupby=groupby,
            listing=listing,
            **kw,
        )

    @http.route(
        ["/my/loans/<int:maintenance_request_id>"],
        type="http",
        auth="user",
        website=True,
    )
    def my_maintenance_request_detail(self, maintenance_request_id: int, **kw) -> Response:
        url = self._BASE_URL
        try:
            maintenance_request_sudo = self._document_check_access("library.loan", maintenance_request_id)
        except MissingError:
            set_flash_message(
                _("The selected loan don't exist."),
                "danger",
            )
            return request.redirect(url)
        except AccessError:
            set_flash_message(
                _("The selected loan don't exist or you don't have access."),
                "danger",
            )
            return request.redirect(url)
        values = self._get_maintenance_request_page_values(maintenance_request_sudo, **kw)
        maintenance_request_action = False
        values.update(
            {
                "_": _,
                "layout": kw.get("layout", "list"),
                "maintenance_request_action_id": maintenance_request_action.id if maintenance_request_action else False,
            }
        )
        return request.render(
            self._TEMPLATE_DETAIL,
            change_previous_next_record_url(values, maintenance_request_sudo, url, self._HISTORY_SESSION_KEY),
        )

