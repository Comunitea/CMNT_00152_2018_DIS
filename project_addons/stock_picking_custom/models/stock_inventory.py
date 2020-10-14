# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, registry, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    validated_by = fields.Many2one('res.users', string='Validado por')

    @api.multi
    def action_validate(self):
        ctx = self._context.copy()
        ctx.update(from_stock_inventory=True)
        return super(StockInventory, self.with_context(ctx)).action_validate()

    def _action_done(self):
        super()._action_done()
        self.write({'validated_by': self.env.user.id})
        return True