odoo.define('website_dismac.collapsable_categories_hover',
        function (require) {
    "use strict";

    var config = require('web.config');

    var sAnimations = require('website.content.snippets.animation');

    sAnimations.registry.websiteSaleCategory = sAnimations.Class.extend({
        // Change id with _custom suffix according new views
        selector: '#o_shop_collapse_category_custom',
        read_events: {
            'click .fa-chevron-right': '_onOpenClick',
            'click .fa-chevron-down': '_onCloseClick',
            //'mouseenter li.nav-item': '_onHoverCategory',
            //'mouseleave li.nav-item': '_onHoverCategoryOut',
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
        /**
         * @private
         * @param {Event} ev
         */
        _onHoverCategory: function (ev) {
            if (config.device.isMobile) {
                return;
            }
            var $fa = $(ev.currentTarget);
            var $i = $fa.find("i");
            if ($i.hasClass('fa-chevron-right')){
                $i.trigger('click');
            }
        },
        /**
         * @private
         * @param {Event} ev
         */
        _onHoverCategoryOut: function (ev) {
            if (config.device.isMobile) {
                return;
            }
            clearTimeout(this.hoverTimer);
            this.hoverTimer = setTimeout(function () {
                var $fa = $(ev.currentTarget);
                var $i = $fa.find("i");
                if ($i.hasClass('fa-chevron-down')){
                    $i.trigger('click');
                }
            }, 200);
        }
    });

})