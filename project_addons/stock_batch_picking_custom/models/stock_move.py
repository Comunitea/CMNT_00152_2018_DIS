# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models

from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):

    _inherit = 'stock.move.line'

    @api.multi
    def _get_sale_order(self):
        for move in self:
            if not move.move_id.sale_line_id:
                lines = move.move_id.move_dest_ids.mapped('sale_line_id')
                if lines:
                    line = lines[0]
            else:
                line = move.move_id.sale_line_id

            move.sale_order = line.order_id

    sale_order = fields.Many2one('sale.order', compute="_get_sale_order")

