# -*- coding: utf-8 -*-
# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

class StockBatchPickingCreator(models.TransientModel):

    _inherit = 'stock.picking.batch.creator'

    auto_fill_done = fields.Boolean('Cantidad hecha', default=True, help ="Si está marcado, pone las cantidades hechas")
    auto_action_assign = fields.Boolean('Reservar auto', default=True, help = "Si esta marcado, hace una reserva automatica al crearlo")

    def apply_autos(self, batchs):
        if self.auto_action_assign:
            batchs.action_assign()
        if self.auto_fill_done:
            ctx = self._context.copy()
            ctx.update(reset=False)
            batchs.with_context(ctx).force_set_qty_done()

    def _prepare_stock_batch_picking(self):
        res = super()._prepare_stock_batch_picking()

        res['auto_fill_done'] = self.auto_fill_done
        return res

    def create_simple_batch(self, domain):
        batchs = super().create_simple_batch(domain=domain)
        self.apply_autos(batchs)
        return batchs

    def create_multiple_batch(self, domain):
        batchs = super().create_multiple_batch(domain=domain)
        self.apply_autos(batchs)
        return batchs

    @api.multi
    def action_create_batch(self):
        ctx = self._context.copy()
        ctx.update(auto_fill_done=self.auto_fill_done, auto_action_assign=self.auto_action_assign)
        return super(StockBatchPickingCreator, self.with_context(ctx)).action_create_batch()