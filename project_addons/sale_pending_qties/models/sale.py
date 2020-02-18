# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def compute_pending_move_lines(self):
        picking_id = self._context.get('picking_id', False)
        for sale in self:
            domain = [('sale_line_id.order_id', '=', sale.id),
                      ('location_dest_id.usage', '=', 'customer'),
                      ('state', 'not in', ('draft', 'cancel', 'done'))]
            if picking_id:
                domain += [('picking_id', '!=', 'picking_id')]
            stock_moves = self.env['stock.move'].search(domain)
            sale.pending_move_lines = stock_moves

    pending_move_lines = fields.One2many('stock.move', string="Lineas pendientes", compute="compute_pending_move_lines")

    @api.multi
    def action_tree_pending_moves(self):
        self.ensure_one()
        action = self.env.ref(
            "stock.stock_move_action"
        ).read()[0]
        tree_view = self.env.ref('sale_pending_qties.view_move_tree_pending_moves')
        action['view_move'] = 'tree'
        action['views'] = [(tree_view.id, 'tree')]
        action['context'] = {'search_default_done': 0, 'search_default_groupby_location_id': 0}
        action["domain"] = [("id", "in", self.pending_move_lines.ids)]
        return action
