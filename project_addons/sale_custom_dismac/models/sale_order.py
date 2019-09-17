# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    #approval_conditions = fields.Boolean('Approval Conditions', default=False)
    show_layout = fields.Boolean(related='type_id.show_layout', readonly=True)
    need_approval = fields.Boolean(related='type_id.need_approval',
                                   readonly=True)

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

    @api.multi
    def action_cancel(self):
        self.write({'active': False,})
        return super(SaleOrder, self).action_cancel()


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

