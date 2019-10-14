# Copyright 2012-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockBatchPickingCreator(models.TransientModel):

    _inherit = 'stock.picking.batch.creator'

    picking_type_id = fields.Many2one('stock.picking.type', 'Picking type')

    @api.model
    def default_get(self, fields_list):
        pics = self.env['stock.picking'].browse(
            self._context.get('active_ids', []))
        if len(pics.mapped('picking_type_id')) > 1:
            raise UserError(_('All pickings must be the same type'))
        return super().default_get(fields_list)

    @api.multi
    def action_create_batch(self):
        res = super().action_create_batch()
        batch = self.env['stock.picking.batch'].browse(res['res_id'])
        batch.picking_type_id = batch.picking_ids.mapped('picking_type_id')[0]
        return res
