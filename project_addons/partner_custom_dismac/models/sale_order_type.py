# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class SaleOrderType(models.Model):
    _inherit = "sale.order.type"

    unclaimable_for = fields.Integer(
        "Days to claim",
        help="Partner won't be claimable for this days after being claimed by another user",
        default=90,
    )
    days_without_order_or_quotation = fields.Integer(
        "Days without order",
        help="Number of days with no order or quotation before the partner becomes claimable",
        default=180,
    )
