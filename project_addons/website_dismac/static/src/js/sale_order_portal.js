odoo.define('website_dismac.sale_order_portal_content_website_dismac', function(require) {

    var rpc = require('web.rpc');
    require('web.dom_ready');
    require('website_sale.website_sale');
    var ajax = require('web.ajax');
    var core = require('web.core');
    require("website.content.zoomodoo");
    var _t = core._t;    
    
    
    // hack to add from sale order portal to cart with json
    $(document).on('click', 'a.js_add_cart_json_sale_order_portal_content', function (ev) {

        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var $input = $link.parent().find("input");
        var product_id = +$input.closest('*:has(input[name="product_id"])').find('input[name="product_id"]').val();

        ajax.jsonRpc("/shop/cart/update_json", 'call', {
            'product_id': parseInt(product_id, 10),
            'add_qty': 1
        }).then(function (data) {
            var $q = $(".my_cart_quantity");
            if (data.cart_quantity) {
                $q.text(data.cart_quantity);
            }
            else {
                window.location = '/shop/cart';
            }
        });

    });

});
