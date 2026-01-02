/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import DynamicSnippetCarousel from "@website/snippets/s_dynamic_snippet_carousel/000";

const DynamicSnippetBooks = DynamicSnippetCarousel.extend({
    selector: '.s_dynamic_snippet_books',

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Gets the category search domain
     *
     * @private
     */
    _getCategorySearchDomain() {
        const searchDomain = [];
        let bookCategoryId = this.$el.get(0).dataset.bookCategoryId;
        if (bookCategoryId && bookCategoryId !== 'all') {
            if (bookCategoryId === 'current') {
                bookCategoryId = undefined;
                const bookCategoryField = $("#book_details").find(".book_category_id");
                if (bookCategoryField && bookCategoryField.length) {
                    bookCategoryId = parseInt(bookCategoryField[0].value);
                }
                if (!bookCategoryId) {
                    this.trigger_up('main_object_request', {
                        callback: function (value) {
                            if (value.model === "library.category") {
                                bookCategoryId = value.id;
                            }
                        },
                    });
                }
            }
            if (bookCategoryId) {
                searchDomain.push(['category_id', '=', parseInt(bookCategoryId)]);
            }
        }
        return searchDomain;
    },
    /**
     * Method to be overridden in child components in order to provide a search
     * domain if needed.
     * @override
     * @private
     */
    _getSearchDomain: function () {
        const searchDomain = this._super.apply(this, arguments);
        searchDomain.push(...this._getCategorySearchDomain());
        const bookTitles = this.$el.get(0).dataset.bookTitles;
        if (bookTitles) {
            const nameDomain = [];
            for (const bookTitle of bookTitles.split(',')) {
                // Ignore empty names
                if (!bookTitle.length) {
                    continue;
                }
                // Search on name, internal reference and barcode.
                if (nameDomain.length) {
                    nameDomain.unshift('|');
                }
                nameDomain.push(...[
                    '|', '|', ['name', 'ilike', bookTitle],
                              ['description', '=', bookTitle],
                              ['isbn', '=', bookTitle],
                ]);
            }
            searchDomain.push(...nameDomain);
        }
        return searchDomain;
    },
    /**
     * Add `bookTemplateId` for book snippets (Accessories, Alternatives and Recently sold).
     *
     *
     * @override
     * @private
     */
    _getRpcParameters: function () {
        const bookTemplateId = $("#book_details").find(".book_template_id");
        return Object.assign(this._super.apply(this, arguments), {
            bookTemplateId: bookTemplateId && bookTemplateId.length ? bookTemplateId[0].value : undefined,
        });
    },
});

publicWidget.registry.dynamic_snippet_books = DynamicSnippetBooks;

export default DynamicSnippetBooks;
