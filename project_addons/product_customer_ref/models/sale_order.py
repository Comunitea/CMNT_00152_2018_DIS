# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    @api.onchange("partner_id")
    def onchange_partner_id(self):
        res = super().onchange_partner_id()

        if self.partner_id and self.partner_id.own_product_codes:
            for line in self.order_line:
                if line.product_id:
                    line.update_product_customer_name(
                        self.partner_id.id, line.product_id.id
                    )
        return res


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    def update_product_customer_name(self, partner_id, product_id):
        domain = [
            ("partner_id", "=", partner_id),
            ("product_id", "=", product_id),
        ]
        value = self.env["product.customer.value"].search(domain, limit=1)
        if value:
            self.name = value.name_get()[0][1]
        return

    @api.multi
    @api.onchange("product_id")
    def product_id_change(self):
        res = super().product_id_change()
        partner_id = self.order_id.partner_id
        if partner_id and partner_id.own_product_codes:
            product_id = self.product_id
            if partner_id and product_id:
                self.update_product_customer_name(partner_id.id, product_id.id)
        return res
