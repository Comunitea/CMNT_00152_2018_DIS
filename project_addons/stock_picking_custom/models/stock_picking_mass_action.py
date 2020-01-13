# Copyright 2014 Camptocamp SA - Guewen Baconnier
# Copyright 2018 Tecnativa - Vicent Cubells
# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, api
from odoo.models import TransientModel


class StockPickingMassAction(TransientModel):
    _inherit = 'stock.picking.mass.action'

    @api.multi
    def mass_action(self):
        self.ensure_one()
        res = super().mass_action()
        if self.transfer:
            not_done = self.picking_ids.filtered(lambda x: x.state != 'done')
            action = self.env.ref('stock.stock_picking_action_picking_type').read()[0]
            action['domain'] = [('id', 'in', not_done.ids)]
            action['context'] = self._context
            return action

