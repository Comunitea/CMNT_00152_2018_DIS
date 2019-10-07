# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    exclude_compute_cost = fields.Boolean(
        'Exclude from compute cost', default=False,
        help="If true, this purchase is no include in cost computes")


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking=picking)
        for val in res:
            val.update(exclude_compute_cost=self.order_id.exclude_compute_cost)
        return res
