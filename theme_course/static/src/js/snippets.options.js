/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";


options.registry.FeaturesColumnsGap = options.Class.extend({
    async _renderCustomXML(uiFragment) {
        const gapRangeEl = uiFragment.querySelector(`we-range[data-param=gap]`);
        if (gapRangeEl) {
            const currentGap = this.$target.data('gap') || 0;
            gapRangeEl.value = currentGap;
            gapRangeEl.dataset.defaultValue = currentGap;
        }
    },
    /**
     * Customizes the gap between feature columns by applying a CSS class.
     *
     * @param {boolean} previewMode - Indicates if the customization is being previewed
     * @param {string} widgetValue - The gap value from the widget
     * @param {Object} params - Additional parameters for customization
     * @returns {Promise<void>}
     */
    async customizeGap(previewMode, widgetValue, params) {
        const gap = parseInt(widgetValue, 10) || 0;
        const $rowBody = this.$target.find('.row.body');
        // Remove all classes starting with 'gap-'
        $rowBody.attr('class', function (i, className) {
            return className.replace(/\bgap-\S+/g, '');
        });
        $rowBody.addClass(`gap-${gap}`);
        this.$target.data('gap', gap);
    },
});