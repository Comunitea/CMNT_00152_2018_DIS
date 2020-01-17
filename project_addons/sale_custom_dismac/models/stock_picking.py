# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from datetime import date


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    type_id = fields.Many2one(comodel_name='sale.order.type', string='Tipo')

    @api.multi
    def refresh_type_from_sale_order(self):
        picks = self.filtered(lambda x: x.sale_id)
        for pick in picks:
            val = {'type_id': pick.sale_id.type_id.id}
            pick.move_lines.write(val)
        picks.write(val)

    @api.multi
    @api.depends('move_lines', 'state','sale_id')
    def get_n_lines(self):
        super().get_n_lines()
        for pick in self:
            if pick.sale_id:
                if pick.sale_id.pending_review:
                    pick.info_str = pick.info_str + " :  PENDIENTE 999"

    @api.depends('move_type', 'move_lines.state', 'move_lines.picking_id')
    @api.one
    def _compute_state(self):
        super()._compute_state()
        if self.move_type == 'one':
            if self.state == 'assigned' and self.sale_id.pending_review:
                self.state = 'confirmed'
                self.all_assigned = False
        else:
             if self.state == 'assigned' and self.sale_id.pending_review:
                self.all_assigned = False

                
