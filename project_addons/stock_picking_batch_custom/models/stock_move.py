# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockMoveLine(models.Model):

    _inherit = "stock.move.line"

    @api.multi
    def _get_sale_order(self):

        for move in self:
            line = move.move_id.mapped(
                "sale_line_id"
            ) or move.move_id.move_dest_ids.mapped("sale_line_id")
            if line:
                move.sale_order = line[0].order_id
                move.partner_id = line[0].order_id.partner_id

    sale_order = fields.Many2one("sale.order", compute="_get_sale_order")
    partner_id = fields.Many2one("res.partner", compute="_get_sale_order")
