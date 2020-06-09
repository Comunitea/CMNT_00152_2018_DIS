# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    exclude_compute_cost = fields.Boolean(
        "Exclude from compute cost",
        default=False,
        help="If true, this purchase is no include in cost computes",
    )

    @api.multi
    def button_approve(self, force=False):
        res = super().button_approve(force)
        for rec in self:
            rec.order_line.mapped('product_id')._set_last_purchase_fixed()
        return res

    @api.multi
    def button_cancel(self):
        res = super().button_cancel()
        for rec in self:
            rec.order_line.mapped('product_id')._set_last_purchase_fixed()
        return res



class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    exclude_compute_cost = fields.Boolean(
        "Exclude from compute cost",
        related='order_id.exclude_compute_cost',
        help="If true, this purchase is no include in cost computes",
        default=False,
        store=True
    )

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking=picking)
        for val in res:
            val.update(exclude_compute_cost=self.order_id.exclude_compute_cost)
        return res
