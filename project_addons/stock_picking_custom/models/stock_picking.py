# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    to_split_process = fields.Boolean('Para dividir', copy=False, default=False)
    number_of_packages = fields.Integer("Nº de paquetes")
    a_atencion = fields.Char('A la atención de:')

    def do_print_picking(self):
        if self and self[0].picking_type_id.code == 'outgoing':
            pickings = self.filtered(lambda p: p.state != 'cancel')
            return self.env.ref('stock.action_report_delivery').report_action(pickings)
        return super().do_print_picking()

    @api.multi
    def _create_backorder(self, backorder_moves=None):
        backorder = super()._create_backorder(backorder_moves=backorder_moves)
        backorder.write({'move_type': 'one'})
        return backorder
    
    @api.multi
    @api.depends('state', 'is_locked', 'batch_id')
    def _compute_show_validate(self):
        super()._compute_show_validate()
        # for pick in self.filtered(lambda x: x.batch_id):
        #     pick.show_validate = False


    @api.multi
    def set_split_process_done(self):
        self.action_toggle_is_locked()
        return True

    def action_toggle_is_locked(self):
        super().action_toggle_is_locked()
        self.to_split_process = not self.is_locked
        if not self.to_split_process:
            self.move_lines.filtered(lambda x: x.to_split_process).write({'to_split_process': False})
        return True

    @api.multi
    def cancel_split_process_done(self):
        self.action_toggle_is_locked()
        return True

    @api.multi
    def split_process_done(self):
        self.ensure_one()
        if self.state != 'done':
            raise ValidationError(_('Solo con albaranes ya hechos'))

        new_moves = self.move_lines.filtered(lambda x: x.to_split_process)

        if new_moves:
            backorder_picking = self.copy({
                    'name': '/',
                    'move_lines': [],
                    'move_line_ids': [],
                    'backorder_id': self.id,
                })
            self.message_post(
                    body=(
                        'Se dividido el albarán <a href="#" '
                        'data-oe-model="stock.picking" '
                        'data-oe-id="%d">%s</a> <hr/>'
                        'y se ha generado <a href="#" '
                        'data-oe-model="stock.picking" '
                        'data-oe-id="%d">%s</a>.'
                    ) % (
                        self.id, self.name,
                        backorder_picking.id,
                        backorder_picking.name
                    )
                )
            new_moves.write({
                    'picking_id': backorder_picking.id,
                })
            new_moves.mapped('move_line_ids').write({
                    'picking_id': backorder_picking.id,
                })

            self.get_n_lines()
            self.compute_picking_qties()
            backorder_picking.get_n_lines()
            backorder_picking.compute_picking_qties()
            self.cancel_split_process_done()
            backorder_picking.cancel_split_process_done()

        """Use to trigger the wizard from button with correct context"""
        # for picking in self:
        #
        #     # Check the picking state and condition before split
        #     if picking.state != 'done':
        #         raise UserError(_('Solo con albaranes ya hechos'))
        #     if all([x.qty_done == 0.0 for x in picking.move_line_ids]):
        #         raise UserError(
        #             _('You must enter done quantity in order to split your '
        #               'picking in several ones.'))
        #
        #     # Split moves considering the qty_done on moves
        #     new_moves = self.env['stock.move']
        #     for move in picking.move_lines:
        #         rounding = move.product_uom.rounding
        #         qty_done = move.quantity_done
        #         qty_initial = move.product_uom_qty
        #         qty_diff_compare = float_compare(
        #             qty_done, qty_initial, precision_rounding=rounding
        #         )
        #         if qty_diff_compare < 0:
        #             qty_split = qty_initial - qty_done
        #             qty_uom_split = move.product_uom._compute_quantity(
        #                 qty_split,
        #                 move.product_id.uom_id,
        #                 rounding_method='HALF-UP'
        #             )
        #             new_move_id = move._split(qty_uom_split)
        #             for move_line in move.move_line_ids:
        #                 if move_line.product_qty and move_line.qty_done:
        #                     # To avoid an error
        #                     # when picking is partially available
        #                     try:
        #                         move_line.write(
        #                             {'product_uom_qty': move_line.qty_done})
        #                     except UserError:
        #                         pass
        #             new_moves |= self.env['stock.move'].browse(new_move_id)
        #
        #     # If we have new moves to move, create the backorder picking
        #     if new_moves:
        #         backorder_picking = picking.copy({
        #             'name': '/',
        #             'move_lines': [],
        #             'move_line_ids': [],
        #             'backorder_id': picking.id,
        #         })
        #         picking.message_post(
        #             body=_(
        #                 'The backorder <a href="#" '
        #                 'data-oe-model="stock.picking" '
        #                 'data-oe-id="%d">%s</a> has been created.'
        #             ) % (
        #                 backorder_picking.id,
        #                 backorder_picking.name
        #             )
        #         )
        #         new_moves.write({
        #             'picking_id': backorder_picking.id,
        #         })
        #         new_moves.mapped('move_line_ids').write({
        #             'picking_id': backorder_picking.id,
        #         })
        #         new_moves._action_assign()