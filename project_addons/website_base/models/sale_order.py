# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):

    _inherit = "sale.order"

    needed_for_min_amount_order = fields.Float('For Min. Amount', compute='_compute_needed_for_min_amount_order', \
        help='Amount needed for min. amount order')
    needed_for_free_shipping = fields.Float('For free Shipping', compute='_compute_needed_for_free_shipping', \
        help='Amount needed for free shipping')

    
    @api.multi
    def find_pending_tier(self):
        tier = self.env['tier.review'].sudo().search([('model', '=', 'sale.order'), ('res_id', '=', self.id), ('status', '=', 'pending')])
        return tier

    @api.multi
    def _compute_needed_for_min_amount_order(self):
        for order in self:
        
            if order.partner_id.avoid_locks or not order.partner_id.min_amount_order:
                order.needed_for_min_amount_order = 0.0

            if order.partner_id.min_amount_order and order.amount_total < order.partner_id.min_amount_order:
                order.needed_for_min_amount_order = order.partner_id.min_amount_order - order.amount_total
            else:
                order.needed_for_min_amount_order = 0.0

    @api.multi
    def _compute_needed_for_free_shipping(self):
        for order in self:
            amount_total_without_delivery = order._compute_amount_total_without_delivery()
            if order.delivery_price:
                if order.delivery_price == 0.0:
                    order.needed_for_free_shipping = 0.0
                elif order.carrier_id and order.carrier_id.price_rule_ids:
                    rules = order.carrier_id.price_rule_ids.filtered(lambda x: x.variable == 'price' and x.list_base_price == 0.0)
                    if rules[0].max_value > amount_total_without_delivery:
                        order.needed_for_free_shipping = rules[0].max_value - amount_total_without_delivery
                    else:
                        order.needed_for_free_shipping = 0.0
                else:
                    if order.carrier_id and order.carrier_id.free_over:
                        if order.carrier_id.amount > amount_total_without_delivery:
                            order.needed_for_free_shipping = order.carrier_id.amount - amount_total_without_delivery
                        else:
                            order.needed_for_free_shipping = 0.0

    def send_lock_alerts(self, errors):        
        ctx = self._context.copy()
        odoo_bot = self.sudo().env.ref("base.partner_root")
        email_from = odoo_bot.email
        user = self.env['res.users'].browse([ctx.get('uid')])
        user_validator = user.order_validator or user.partner_id.order_validator
        if user_validator:
            self.env['mail.mail'].create({
                'email_from': email_from,
                'reply_to': email_from,
                'email_to': user_validator.email,
                'subject': _("Order Locked: {}".format(self.name)),
                'body_html': _("""
                    <p>The order {} is locked.</p>
                    <p>{}</p>
                    <p></p>
                    <p>&nbsp;</p>
                    <p><span style="color: #808080;">
                    This is an automated message please do not reply.
                    </span></p>
                    """).format(self.name, errors),
                'auto_delete': True,
            })