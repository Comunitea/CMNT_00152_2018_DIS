# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _


class ProductCustomerInfo(models.Model):
    _inherit = "product.customerinfo"

    min_product_qty = fields.Integer(_('Min. Product Qty'), default=1,
        help=_('Minimum product quantity to place an order.'))