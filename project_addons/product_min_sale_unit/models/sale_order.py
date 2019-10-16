# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    category_id = fields.Many2one(
        related="product_id.category_id", readonly=True
    )
    uom_factor = fields.Float(
        related="product_id.min_sale_unit_id.factor", readonly=True
    )

    @api.onchange("product_id")
    def product_id_change_min_sale_unit(self):
        if self.product_id and self.product_id.min_sale_unit_id:
            res = {}
            min_sale_unit_id = self.product_id.min_sale_unit_id
            domain = [
                ("category_id", "=", self.product_id.uom_id.category_id.id),
                ("factor", "<=", min_sale_unit_id.factor),
            ]
            res["domain"] = {"product_uom": domain}
            product_uom = self.env["uom.uom"].search(
                domain, limit=1, order="factor desc"
            )
            if product_uom:
                self.product_uom = product_uom
            return res
