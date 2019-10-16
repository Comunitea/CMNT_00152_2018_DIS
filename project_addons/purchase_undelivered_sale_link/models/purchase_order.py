# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from datetime import datetime, timedelta


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def get_unreceived_sale_lines(self):
        tree_view = self.env.ref(
            "purchase_undelivered_sale_link.view_purchase_delivery_report_tree"
        )
        if self._context.get("product_id", False):
            domain = [("product_id", "=", self.product_id.id)]
        else:
            domain = [
                (
                    "product_id",
                    "in",
                    self.mapped("order_line").mapped("product_id").ids,
                )
            ]

        return {
            "name": "Sales delivery report",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "purchase.undelivered.link.report",
            "views": [(tree_view.id, "tree")],
            "domain": domain,
        }


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def get_unreceived_sale_lines(self):
        return self.order_id.get_unreceived_sale_lines()
