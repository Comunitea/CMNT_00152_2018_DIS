# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, exceptions, _


class ApplyGlobalDiscount(models.TransientModel):

    _name = 'apply.global.discount'

    discount = fields.Float('Discount(%)')

    @api.multi
    def apply_discount(self):
        self.ensure_one()
        if not self._context.get('active_model'):
            return {'type': 'ir.actions.act_window_close'}
        obj = self.env[self._context['active_model']].browse(
            self._context.get('active_id', False))
        if self._context['active_model'] == 'sale.order':
            lines = obj.order_line
        elif self._context['active_model'] == 'account.invoice':
            lines = obj.invoice_line_ids
        for line in lines:
            if self.discount != 0:
                line.discount = self.discount
            else:
                line.discount = 0
        if self._context['active_model'] == 'account.invoice':
            obj.compute_taxes()
        return {'type': 'ir.actions.act_window_close'}
