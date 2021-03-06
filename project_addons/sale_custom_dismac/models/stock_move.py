# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields
from datetime import date


class StockMove(models.Model):

    _inherit = 'stock.move'

    type_id = fields.Many2one(comodel_name='sale.order.type', string='Tipo')

    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        if self.type_id:
            vals['type_id'] = self.type_id.id
        return vals

    def _action_done(self):
        result = super(StockMove, self)._action_done()
        for move in self.filtered(lambda x: x.sale_line_id):
            if move.state == 'done':
                qty = 0.0
                line = move.sale_line_id
                if move.location_dest_id.usage == "customer":
                    if not move.origin_returned_move_id or \
                            (move.origin_returned_move_id and
                                move.to_refund):
                        qty = move.product_uom._compute_quantity(
                            move.product_uom_qty, line.product_uom)
                elif move.location_dest_id.usage != "customer" and \
                        move.to_refund:
                    qty = -move.product_uom._compute_quantity(
                        move.product_uom_qty, line.product_uom)
                if qty:
                    self.env['sale.order.line.delivery'].create({
                        'line_id': line.id,
                        'quantity': qty,
                        'delivery_date': date.today(),
                        'move_id': move.id
                    })
        return result
