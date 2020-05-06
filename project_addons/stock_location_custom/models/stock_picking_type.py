# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

class StockPickingType(models.Model):

    _inherit = 'stock.picking.type'

    # auto_fill_operation = fields.Boolean(
    #     string="Auto fill operations",
    #     help="To auto fill done quantity in picking document.\n"
    #          "- If checked, auto fill done quantity automatically\n"
    #          "- If unchecked, show button AutoFill"
    #          " for user to do the auto fill manually",
    # )