# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models

from odoo.exceptions import ValidationError
from pprint import pprint

class StockBatchPicking(models.Model):

    _inherit = 'stock.batch.picking'

    @api.depends('picking_ids.picking_type_id')
    @api.multi
    def _get_picking_type(self):
        for batch in self:
            batch.picking_type_id = batch.picking_ids and batch.picking_ids[0].picking_type_id or False

    picking_type_id = fields.Many2one('stock.picking.type', compute="_get_picking_type", store=True)

    @api.constrains('picking_ids')
    def _check_type(self):
        if len(self.picking_ids.mapped('picking_type_id')) > 1:
            raise ValidationError(_("All pìckings in batch must be same type"))


    @api.multi
    def write(self, vals):
        pprint (vals)

        return super().write(vals)