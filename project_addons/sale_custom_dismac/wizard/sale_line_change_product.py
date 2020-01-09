# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleLineChangeProduct(models.TransientModel):

    _name = "sale.line.change.product"

    product_id = fields.Many2one("product.product", required=True)

    def change_product(self):
        order_line = self.env["sale.order.line"].browse(
            self._context.get("active_id")
        )
        order_line.write({"product_id": self.product_id.id})
