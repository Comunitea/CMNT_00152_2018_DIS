# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.onchange('product_id')
    def product_id_change(self):
        res = super().product_id_change()
        customer_price = (
                    self.env["customer.price"].get_customer_price(
                        self.partner_id, self.product_id, self.product_uom_qty
                    )
                )
        if not customer_price:
            categ_dis = self.env["category.discount"].get_customer_discount(
                        self.partner_id, self.product_id.categ_id.id
                    )
            if categ_dis:
                self.discount = categ_dis[0].discount
        return res