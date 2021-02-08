$(document).ready(function() {
    // zoom slider
    $('.zoomContainer').remove();
    $('.product_detail_img').elevateZoom({
        constrainType: "height",
        constrainSize: 274,
        zoomType: "lens",
        containLensZoom: true,
        cursor: 'pointer'
    });
    $('.js_main_product input.product_id').change(function(){
    $('.zoomContainer').remove();
    $('.product_detail_img').elevateZoom({
        constrainType: "height",
        constrainSize: 274,
        zoomType: "lens",
        containLensZoom: true,
        cursor: 'pointer'
    });
    $.getScript("/dismac_ecommerce/static/src/js/zoom.js");
    })

});

