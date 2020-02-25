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
            not_stock = sum(x.not_stock for x in move.move_line_ids)
            # Si ya se ha creado, entonces salimos
            if not_stock > 0:
                continue
            not_stock = move.product_uom_qty - move.reserved_availability

            ## Si un movimiento ya tiene lineas creadas se salta ala siguiente
            if move.move_line_ids:
                last_move = move.move_line_ids[-1]
                sugested_location = last_move.location_id
                sugested_location_dest = last_move.location_dest_id
            else:
                sugested_location = move.location_id.get_putaway_strategy(move.product_id) or move.location_id
                sugested_location_dest = move.location_dest_id.get_putaway_strategy(move.product_id) or move.location_dest_id

            if move.product_id.tracking == 'serial':
                new_serial_lines = self.env['stock.move.line']
                vals = move._prepare_move_line_vals()
                vals.update(not_stock=1,
                            product_uom_qty=0,
                            location_dest_id=sugested_location_dest.id,
                            location_id=sugested_location.id)
                for l in range(0, not_stock):
                    new_serial_lines |= self.env['stock.move.line'].create(vals)
                    move.write({'move_line_ids': [(4, new_serial_lines.ids)]})
            else:

                vals = move._prepare_move_line_vals()
                vals.update(not_stock=not_stock,
                            product_uom_qty=0,
                            location_dest_id=sugested_location_dest.id,
                            location_id=sugested_location.id)

                if move.move_line_ids:
                    move_line = self.env['stock.move.line'].create(vals)
                    move.write({
                        'move_line_ids': [(4, move_line.id)]})


class StockMoveLine(models.Model):

    _inherit='stock.move.line'

    not_stock = fields.Float('Not Reserved', default=0.0, digits=dp.get_precision('Product Unit of Measure'), required=True)
    sale_line_id = fields.Many2one(related='move_id.sale_line_id', string='Venta')
    src_removal_priority = fields.Integer(related='location_id.removal_priority', store=True)
    dest_removal_priority = fields.Integer(related='location_dest_id.removal_priority', store=True)
    ordered_qty = fields.Float(string="C. Ordenada", compute="_get_ordered_qty")
    empty_line = fields.Boolean('Creada vacía')

    @api.multi
    def _get_ordered_qty(self):
        for sml in self.filtered(lambda x: not x.not_stock):
            sml.ordered_qty = sml.move_id.product_uom_qty

    @api.onchange('lot_id')
    def onchange_serial_lot_id(self):
        if self._context.get('change_serial', True):
            if self.product_id.tracking == 'serial':
                if self.lot_id:
                    self.qty_done = 1
                else:
                    self.qty_done = 0

    @api.multi
    def force_assigned_qty_done(self, reset=True, field='product_uom_qty'):
        if reset:
            return super().force_assigned_qty_done(reset=reset, field=field)
        else:
            return super(StockMoveLine, self.filtered(lambda x: not x.empty_line)).force_assigned_qty_done(reset=reset, field=field)
