/* Hook to work with view that now add product images in products list view */
odoo.define('website_base.website_sale_category', function (require) {
'use strict';

    var sAnimations = require('website.content.snippets.animation');

    sAnimations.registry.websiteSaleCategory = sAnimations.Class.extend({
        // Change id with _custom suffix according new views
        selector: '#o_shop_collapse_category_custom',
        read_events: {
            'click .fa-chevron-right': '_onOpenClick',
            'click .fa-chevron-down': '_onCloseClick',
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         * @param {Event} ev
         */
        _onOpenClick: function (ev) {
            var $fa = $(ev.currentTarget);
            $fa.parent().siblings().find('.fa-chevron-down:first').click();
            // Changed parent by closets
            // $fa.parents('li').find('ul:first').show('normal');
            $fa.closest('li').find('ul:first').show('normal');
            $fa.toggleClass('fa-chevron-down fa-chevron-right');
        },
        /**
         * @private
         * @param {Event} ev
         */
        _onCloseClick: function (ev) {
            var $fa = $(ev.currentTarget);
            // Changed parent by closets
            // $fa.parent().find('ul:first').hide('normal');
            $fa.closest('li').find('ul:first').hide('normal');
            $fa.toggleClass('fa-chevron-down fa-chevron-right');
        },
    });
});