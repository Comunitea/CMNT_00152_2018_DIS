# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    min_amount_for_free_delivery = fields.Float(
        "Minimum amount for free delivery", store=True, default=0.0
    )
    customer_ref = fields.Char("Referencia cliente Dismac")

    def get_purchase_lines(self):
        model_data = self.env["ir.model.data"]

        tree_view = model_data.get_object_reference(
            "purchase_custom_dismac", "purchase_custom_tree"
        )
        search_view = model_data.get_object_reference(
            "purchase_custom_dismac", "purchase_custom_search"
        )
        domain = [("partner_id", "=", self.id)]
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
                "context": {"search_default_draft": 1},
            }
        return value
