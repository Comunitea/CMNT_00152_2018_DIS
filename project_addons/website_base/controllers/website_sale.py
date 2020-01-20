# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleLocks(WebsiteSale):
    
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        order = request.website.sale_get_order()

        if order.locked:
            render_values = self._get_shop_payment_values(order, **post)

            reason_list = []
            if order.risk_lock:
                reason_list.append(_("Risk"))
            if order.unpaid_lock:
                reason_list.append(_("Unpaid"))
            if order.margin_lock:
                reason_list.append(_("Margin"))
            if order.shipping_lock:
                reason_list.append(_("No reach shipping min"))
            if order.amount_lock:
                reason_list.append(_("No reach min amount order"))

            reasons = ", ".join(reason_list)

            errors = [
                _("This order can not be finished becaused is locked"),
                reasons
            ]

            render_values['errors'].append(errors)
            return request.render("website_sale.payment", render_values)

        return super(WebsiteSaleLocks, self).payment(**post)