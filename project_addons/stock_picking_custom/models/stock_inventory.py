# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, registry, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    @api.multi
    def action_validate(self):
        ctx = self._context.copy()
        ctx.update(from_stock_inventory=True)
        return super(StockInventory, self.with_context(ctx)).action_validate()