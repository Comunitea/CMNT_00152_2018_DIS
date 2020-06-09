odoo.define('website_sale_options.website_base', function (require) {
'use strict';

    var weContext = require('web_editor.context');
    var WebsiteSaleOptions = require('website_sale_options.website_sale');
    
    WebsiteSaleOptions.include({
        /**
         * @override
         */
        _onModalSubmit: function (goToShop){
            var customValues = JSON.stringify(
                this.optionalProductsModal.getSelectedProducts()
            );
    
            this.$form.ajaxSubmit({
                url:  '/shop/cart/update_option',
                data: {
                    lang: weContext.get().lang,
                    custom_values: customValues
                },
                success: function (quantity) {
                    if (goToShop) {
                        //var path = window.location.pathname.replace(/shop([\/?].*)?$/, "shop/cart");
                        window.location.pathname = "shop/cart";
                    }
                    var $quantity = $(".my_cart_quantity");
                    $quantity.parent().parent().removeClass("d-none", !quantity);
                    $quantity.html(quantity).hide().fadeIn(600);
                }
            });
        },
    });
});
