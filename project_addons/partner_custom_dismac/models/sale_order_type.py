# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'sale.order.type'

    unclaimable_for = fields.Integer('days after being claimed', help="Partner won't be claimable for this days after being claimed by another user", store=True, default=90)
    days_without_order_or_quotation = fields.Integer('days_without_order_or_quotation', help="Number of days with no order or quotation before the partner becomes claimable", store=True, default=180)