# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockMoveLine(models.Model):

    _inherit = "stock.move.line"

    sale_order = fields.Many2one(related='move_id.sale_line_id.order_id')
    partner_id = fields.Many2one(related='move_id.partner_id')
    p_color = fields.Char('COlor', compute='get_p_color')

    @api.multi
    def get_p_color(self):
        for line in self:
            if line.qty_done == line.product_uom_qty:
                p_color = '10' #green
            elif line.qty_done > 0 and line.qty_done != line.product_uom_qty:
                p_color = '1' #red
            else:
                p_color = '4' #light blue
            line.p_color = p_color

    @api.multi
    def action_change_qty(self):
        inc = self._context.get('inc', False)
        if inc == 1:
            self.qty_done += inc
        elif inc==-1:
            self.qty_done = max(0, self.qty_done + inc)

