odoo.define('dismac_ecommerce.ProductConfiguratorMixin', function (require) {
'use strict';
var sAnimations = require('website.content.snippets.animation');
var core = require('web.core');
var QWeb = core.qweb;
var ajax = require('web.ajax');
var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
sAnimations.registry.WebsiteSale.include({
    _onChangeCombination: function (){
        this._super.apply(this, arguments);
        this._onChangeCombinationImage.apply(this, arguments);
    },
    _onChangeCombinationImage: function (ev, $parent, combination) {
    var isMainProduct = combination.product_id &&
        ($parent.is('.js_main_product') || $parent.is('.main_product')) &&
        combination.product_id === parseInt($parent.find('.product_id').val());

    if (!this.isWebsite || !isMainProduct){
        return;
    }
	if(combination.product_id){
           		$.get("/variant_change_images",{'product': combination.product_id}).then(function data(data){
         			$('.product-img-box').empty().append(data);
         			$('#pro_detail_zoom').owlCarousel({})
         			$.getScript("/dismac_ecommerce/static/src/js/zoom.js");
         			$.getScript("/dismac_ecommerce/static/src/js/product_image_gallery_js.js");

        		})


        }


},
})


return sAnimations.registry.WebsiteSaleOptionsImage;
    });
