odoo.define("dismac_ecommerce.as_home_banner", function (require) {
    "use strict";

    window.onload = function () {
        let themeslider = document.querySelector(".theme-slider"),
            elemOne = document.querySelector("#img-1"),
            elemTwo = document.querySelector("#img-2");

        if (themeslider) {
            themeslider.addEventListener("mousemove", function (e) {
                var pageX = e.clientX - window.innerWidth / 1,
                    pageY = e.clientY - window.innerHeight / 1;
                elemOne.style.transform =
                    "translateX(" +
                    (7 + pageX / 150) +
                    "%) translateY(" +
                    (1 + pageY / 150) +
                    "%)";
                elemTwo.style.transform =
                    "translateX(" +
                    (7 + pageX / 150) +
                    "%) translateY(" +
                    (1 + pageY / 150) +
                    "%)";
            });
        };
    };
});
