odoo.define('dismac_ecommerce.clean', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    $(document).ready(function(){
        $("body").on('click','.remove_cart',function (ev){
            ev.preventDefault();
            ajax.jsonRpc("/shop/cart/clean_cart", 'call', {}).then(function(data){
                location.reload();
                return;
            });
        return false;
        });
    });
    $(document).ready(function(){
    if($(".oe_website_sale").length === 0){
        $("div#wrap").addClass("oe_website_sale");
    }
    $(".o_twitter, .o_facebook, .o_linkedin, .o_google").on('click', function(event){
        var url = '';
        var product_title_complete = $('#product_details h1').html().trim() || '';
        if ($(this).hasClass('o_twitter')){
            url = 'https://twitter.com/intent/tweet?tw_p=tweetbutton&text=Amazing product : '+product_title_complete+"! Check it live: "+window.location.href;
        } else if ($(this).hasClass('o_facebook')){
            url = 'https://www.facebook.com/sharer/sharer.php?u='+window.location.href;
        } else if ($(this).hasClass('o_linkedin')){
            url = 'https://www.linkedin.com/shareArticle?mini=true&url='+window.location.href+'&title='+product_title_complete;
        } else if ($(this).hasClass('o_google')){
            url = 'https://plus.google.com/share?url='+window.location.href;
        } else{}
        window.open(url, "", "menubar=no, width=500, height=400");
    });
    });
});
