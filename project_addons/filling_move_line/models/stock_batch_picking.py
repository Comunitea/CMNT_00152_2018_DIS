# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare

class StockBatchPicking(models.Model):
    _inherit = 'stock.picking.batch'


    @api.multi
    def show_helping_tree(self):

        precision_digits = self.env[
            'decimal.precision'].precision_get('Product Unit of Measure')
        self.ensure_one()
        sml = self.env['stock.move.line']
        ## Creo move_lines a cero
        self.move_lines.create_empty_move_lines()

        ctx = self._context.copy()
        ctx.update(hide_lot_id=not any(x.product_id.tracking == 'serial' for x in self.move_lines))
        if self.picking_type_id.code == 'incoming':
            ctx.update(hide_location_id=True)
        elif self.picking_type_id.code == 'outoging':
            ctx.update(hide_location_dest_id=True)
        else:
            if self.picking_type_id.default_location_src_id and not self.picking_type_id.default_location_src_id.child_ids:
                ctx.update(hide_location_id=True)
            if self.picking_type_id.default_location_dest_id and not self.picking_type_id.default_location_dest_id.child_ids:
                ctx.update(hide_location_dest_id=True)


        action = self.env.ref('filling_move_line.action_view_filling_move_line').read()[0]
        action['views'] = [
            (self.env.ref('filling_move_line.view_filling_move_line').id, 'tree'),
        ]
        ids = self.mapped('move_lines').mapped('move_line_ids').ids
        action['domain'] = [('id', 'in', ids)]
        action['context'] = ctx
        return action

