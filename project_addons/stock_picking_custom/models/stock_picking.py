# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'


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