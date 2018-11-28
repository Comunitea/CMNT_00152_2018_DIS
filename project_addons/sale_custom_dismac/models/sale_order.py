# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    approval_conditions = fields.Boolean('Approval Conditions')

    @api.multi
    def action_confirm(self):
        """
        Check if order requires client_order_ref
        """
        for order in self:
            if order.partner_id.require_num_order \
                    and not order.client_order_ref:
                msg = _('The customer for this order requires a customer \
                        reference number')
                raise UserError(msg)
        res = super(SaleOrder, self).action_confirm()
        return res

    def onchange_partner_id(self):
        """
        Look at the partner for changing the invoice policy
        """
        import ipdb; ipdb.set_trace()
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id and self.partner_id.whole_orders:
            self.update({'picking_policy': 'one'})
        if not self.type_id.use_partner_agent:
            self.user_id = self.env.uid
        return res
