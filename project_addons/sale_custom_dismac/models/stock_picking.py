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
