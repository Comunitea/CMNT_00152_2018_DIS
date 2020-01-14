# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from datetime import timedelta


class ProductProduct(models.Model):
    _inherit = "product.product"

    last_60_days_sales = fields.Float()

    @api.model
    def compute_last_60_days_sales(self, products=False):
        sixty_days_ago = fields.Datetime.now() + timedelta(days=-60)
        if not products:
            products = self.search([("type", "!=", "service")])
        for product in products:
            sale_lines = self.env["sale.order.line"].search(
                [
                    ("product_id", "=", product.id),
                    ("order_id.date_order", ">=", sixty_days_ago),
                ]
            )
            product.last_60_days_sales = sum(
                sale_lines.mapped("product_uom_qty")
            )

    def button_compute_last_60_days_sales(self):
        self.compute_last_60_days_sales(self)

    def get_unreceived_items(self):
        model_data = self.env["ir.model.data"]

        tree_view = model_data.get_object_reference(
            "purchase_custom_dismac", "purchase_custom_tree"
        )
        search_view = model_data.get_object_reference(
            "purchase_custom_dismac", "purchase_custom_search"
        )
        domain = [("product_id", "=", self.id)]
        value = {}
        for call in self:
            value = {
                "name": _("Purchase order lines"),
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "purchase.order.line",
                "views": [(tree_view and tree_view[1] or False, "tree")],
                "type": "ir.actions.act_window",
                "domain": domain,
                "search_view_id": search_view and search_view[1] or False,
                "context": {"search_default_not_delivered": 1},
            }
        return value
