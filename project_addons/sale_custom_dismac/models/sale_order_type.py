# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrderType(models.Model):
    _inherit = 'sale.order.type'

    show_layout = fields.Boolean()
    need_approval = fields.Boolean(default=False)
    use_partner_agent = fields.Boolean('Use partner commercial')
