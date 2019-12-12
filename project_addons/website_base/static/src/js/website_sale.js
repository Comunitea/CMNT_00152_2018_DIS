odoo.define('website_base.website_sale_category', function (require) {
    'use strict';

    var sAnimations = require('website.content.snippets.animation');

    sAnimations.registry.websiteSaleCategory = sAnimations.Class.extend({
        selector: '#o_shop_collapse_category',
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
            $fa.parents('li').find('ul:first').show('normal');
            $fa.toggleClass('fa-chevron-down fa-chevron-right');
        },
        /**
         * @private
         * @param {Event} ev
         */
        _onCloseClick: function (ev) {
            var $fa = $(ev.currentTarget);
            $fa.parent().find('ul:first').hide('normal');
            $fa.toggleClass('fa-chevron-down fa-chevron-right');
        },
    });
});

odoo.define('website_base.website_sale', function (require) {
    'use strict';

    var utils = require('web.utils');
    var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
    var core = require('web.core');
    var config = require('web.config');
    var sAnimations = require('website.content.snippets.animation');
    require("website.content.zoomodoo");

    var _t = core._t;

    sAnimations.registry.WebsiteSale = sAnimations.Class.extend(ProductConfiguratorMixin, {
        selector: '.oe_website_sale',
        read_events: {
            'submit .o_website_sale_search': '_onSubmitSaleSearch',
        },
        /**
         * @private
         * @param {Event} ev
         */
        _onSubmitSaleSearch: function (ev) {
            if (!this.$('.dropdown_sorty_by').length) {
                return;
            }
            var $this = $(ev.currentTarget);
            if (!ev.isDefaultPrevented() && !$this.is(".disabled")) {
                ev.preventDefault();
                var oldurl = $this.attr('action');
                oldurl += (oldurl.indexOf("?")===-1) ? "?" : "";
                var search = $this.find('input.search-query');
                window.location = oldurl + '&' + search.attr('name') + '=' + encodeURIComponent(search.val());
            }
        },
    });
});
