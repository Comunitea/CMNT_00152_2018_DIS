# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PurchaseOrderLineConfirmChanges(models.TransientModel):

    _name = "purchase.order.line.confirm.changes"

    order_lines = fields.Many2many("purchase.order.line", readonly=True)

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        active_ids = self._context.get("active_ids", False)
        res["order_lines"] = [(6, 0, active_ids)]
        return res

    def confirm(self):
        change_lines = self.order_lines.filtered(
            lambda r: r.state == "draft" and r.new_partner_id is not False
        )
        orders = change_lines.mapped("order_id")
        for partner in change_lines.mapped("new_partner_id"):
            partner_lines = change_lines.filtered(
                lambda r: r.new_partner_id == partner
            )
            new_purchase = self.env["purchase.order"].search(
                [("partner_id", "=", partner.id), ("state", "=", "draft")],
                limit=1,
            )
            if not new_purchase:
                new_purchase = self.env["purchase.order"].create(
                    {"partner_id": partner.id}
                )
            partner_lines.write(
                {"order_id": new_purchase.id, "new_partner_id": False}
            )
        for order in orders:
            if not order.order_line:
                order.button_cancel()
                order.unlink()
