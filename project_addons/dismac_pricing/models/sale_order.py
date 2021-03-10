# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def create_customer_prices(self):
        for line in self.order_line:
            custom_price = self.env["customer.price"].get_customer_price_rec(
                self.partner_id, line.product_id, line.product_uom_qty
            )
            if custom_price:
                custom_price.date_end = date.today()
            self.env["customer.price"].create(
                {
                    "product_id": line.product_id.id,
                    "partner_id": self.partner_id.id,
                    "price": line.price_unit,
                }
            )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("product_uom", "product_uom_qty")
    def product_uom_change(self):

        res = super().product_uom_change()
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
        if price_and_discount.get("promotion", False):
            self.discount = 0
        else:
            if not self.discount:
                self.discount = price_and_discount["discount"]
        return res
