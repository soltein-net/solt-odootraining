/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";
import s_dynamic_snippet_carousel_options from "@website/snippets/s_dynamic_snippet_carousel/options";

import wUtils from "@website/js/utils";

const alternativeSnippetRemovedOptions = [
    'filter_opt', 'book_category_opt', 'book_titles_opt',
]

const dynamicSnippetBooksOptions = s_dynamic_snippet_carousel_options.extend({

    /**
     *
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.modelNameFilter = 'library.book';
        const bookTemplateId = this.$target.closest("#wrapwrap").find("input.book_template_id");
        this.hasbookTemplateId = bookTemplateId.val();
        this.bookCategories = {};
        this.orm = this.bindService("orm");
    },
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Fetches product categories.
     * @private
     * @returns {Promise}
     */
    _fetchbookCategories: function () {
        return this.orm.searchRead("library.category", wUtils.websiteDomain(this), ["id", "name"]);
    },
    /**
     *
     * @override
     * @private
     */
    _renderCustomXML: async function (uiFragment) {
        await this._super.apply(this, arguments);
        await this._renderBookCategorySelector(uiFragment);
    },
    /**
     * Renders the product categories option selector content into the provided uiFragment.
     * @private
     * @param {HTMLElement} uiFragment
     */
    _renderBookCategorySelector: async function (uiFragment) {
        const bookCategories = await this._fetchbookCategories();
        for (let index in bookCategories) {
            this.bookCategories[bookCategories[index].id] = bookCategories[index];
        }
        const bookCategoriesSelectorEl = uiFragment.querySelector('[data-name="book_category_opt"]');
        return this._renderSelectUserValueWidgetButtons(bookCategoriesSelectorEl, this.bookCategories);
    },
    /**
     * @override
     * @private
     */
    _setOptionsDefaultValues: function () {
        this._setOptionValue('bookCategoryId', 'all');
        this._super.apply(this, arguments);
    },
});

options.registry.dynamic_snippet_books = dynamicSnippetBooksOptions;

export default dynamicSnippetBooksOptions;
