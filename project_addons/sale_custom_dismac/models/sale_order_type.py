# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrderType(models.Model):
    _inherit = "sale.order.type"

    need_approval = fields.Boolean(default=False)
    use_partner_agent = fields.Boolean("Use partner commercial")
    no_change_price = fields.Boolean("No change price")
    web = fields.Boolean("Use in web (Only for online Payments)")
