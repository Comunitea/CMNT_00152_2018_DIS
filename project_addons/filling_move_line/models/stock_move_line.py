# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

class StockMove(models.Model):

    _inherit = 'stock.move'

    @api.multi
    def create_empty_move_lines(self):
        for move in self.filtered(lambda x: x.state in ('confirmed', 'partially_available')):
            if not move.move_line_ids.filtered(lambda x: x.not_stock > 0.00):
                qty = move.product_uom_qty - move.reserved_availability
                if move.product_id.tracking != 'serial':

                    vals = move._prepare_move_line_vals()
                    vals.update(not_stock=qty)
                    move_line = self.env['stock.move.line'].create(vals)
                    move.write({'move_line_ids': [(4, move_line.id)]})
                else:
                    new_sml = self.env['stock.move.line']
                    for i in range(0, int(qty)):

                        vals = move._prepare_move_line_vals()
                        vals.update(not_stock=1)
                        new_sml |= self.env['stock.move.line'].create(vals)

                    move.write({'move_line_ids': [(4, new_sml.ids)]})




class StockMoveLine(models.Model):

    _inherit='stock.move.line'

    not_stock = fields.Float('Not Reserved', default=0.0, digits=dp.get_precision('Product Unit of Measure'), required=True)

    @api.onchange('lot_id')
    def onchange_serial_lot_id(self):
        if self._context.get('change_serial', True):
            if self.product_id.tracking == 'serial':
                if self.lot_id:
                    self.qty_done = 1
                else:
                    self.qty_done = 0

