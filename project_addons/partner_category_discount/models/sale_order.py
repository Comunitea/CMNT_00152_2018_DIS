# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.onchange("product_id")
    def product_id_change(self):
        res = super().product_id_change()
        date = self.order_id.date_order or fields.Date.context_today(self)

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id,
        )

        price_and_discount = product._get_price_and_discount(
            self.product_uom_qty, self.partner_id, date
        )
        self.price_unit = price_and_discount["price"]
        if not self.discount:
            self.discount = price_and_discount["discount"]
        return res
