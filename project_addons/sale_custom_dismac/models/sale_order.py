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
        res = super().action_confirm()
        return res

    def set_user_id(self):
        if self.type_id.use_partner_agent:
            user = self.partner_id.user_id
            if not self.partner_id.is_company and not user:
                user = self.partner_id.commercial_partner_id.user_id
            self.user_id = user
        else:
            self.user_id = self.env.uid

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Look at the partner for changing the invoice policy
        """
        res = super().onchange_partner_id()
        if self.partner_id and self.partner_id.whole_orders:
            self.update({'picking_policy': 'one'})
        self.set_user_id()
        return res

    @api.onchange('type_id')
    def onchange_type_id_user_id(self):
        self.set_user_id()

