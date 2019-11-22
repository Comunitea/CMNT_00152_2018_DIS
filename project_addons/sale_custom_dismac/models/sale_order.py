# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .res_partner import PROCUREMENT_PRIORITIES

class SaleOrder(models.Model):

    _inherit = "sale.order"

    # @api.multi
    # @api.depends('order_line')
    # def _compute_sale_order_lines_count(self):
    #     for order in self:
    #         order.order_lines_count = len(order.order_line)

    # order_lines_count = fields.Integer(
    #     'Line count', compute='_compute_sale_order_lines_count')

    need_approval = fields.Boolean(
        related="type_id.need_approval", readonly=True
    )
    priority = fields.Selection(PROCUREMENT_PRIORITIES, 'Priority', default='1')

    @api.multi
    def action_confirm(self):
        """
        Check if order requires client_order_ref
        """
        for order in self:
            if (
                order.partner_id.require_num_order
                and not order.client_order_ref
            ):
                msg = _(
                    "The customer for this order requires a customer \
                        reference number"
                )
                raise UserError(msg)
        res = super().action_confirm()
        return res

    @api.multi
    def action_draft(self):
        self.write({"active": True})
        return super(SaleOrder, self).action_draft()

    def set_user_id(self):
        if self.type_id.use_partner_agent:
            user = self.partner_id.user_id
            if not self.partner_id.is_company and not user:
                user = self.partner_id.commercial_partner_id.user_id
            self.user_id = user
        else:
            self.user_id = self.env.uid

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """
        Look at the partner for changing the invoice policy
        """
        res = super().onchange_partner_id()
        val = {}
        if self.partner_id:
            if self.partner_id.whole_orders:
                val["picking_policy"] = "one"
            val["priority"] = self.partner_id.priority
        self.update(val)
        self.set_user_id()
        return res

    @api.onchange("type_id")
    def onchange_type_id_user_id(self):
        self.set_user_id()
    
    # @api.multi
    # def action_view_order_lines(self):
    #     self.ensure_one()
    

    #     # model_data = self.env['ir.model.data']
    #     # tree_view = model_data.get_object_reference(
    #     #     'sale_custom_dismac', 'sale_order_line_tree_view')
    #     tree_view_name = 'sale_custom_dismac.sale_order_line_tree_view'
    #     tree_view = self.env.ref(tree_view_name)


    #     action = self.env.ref(
    #         'sale_custom_dismac.sale_order_line_tree_view_action').read()[0]

    #     action['views'] = {
    #         (tree_view and tree_view.id or False, 'tree')}

    #     action['domain'] = [('order_id', '=', self.id)]

    #     action['context'] = {
    #         'default_order_id': self.id,
    #         'partner_id': self.partner_id.id,
    #         'pricelist': self.pricelist_id,
    #         'company_id': self.company_id.id,
    #         'type_id': self.type_id.id,
    #     }
    #     action.update(
    #         {'tax_id': {'domain': [('type_tax_use', '=', 'sale'),
    #                                ('company_id', '=', self.company_id)]}}
    #          )


    #     return action


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    notes = fields.Text('Advanced Description')

    @api.multi
    def duplicate_line(self):
        self.ensure_one()
        self.copy({'order_id': self.order_id.id})