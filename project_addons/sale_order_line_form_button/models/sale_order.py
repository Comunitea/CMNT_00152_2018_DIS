# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import fields, models, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    order_partner_id = fields.Many2one(
        'res.partner', related='order_id.partner_id', readonly=True)
    order_pricelist_id = fields.Many2one(
        'product.pricelist', related='order_id.pricelist_id', readonly=True)
    order_company_id = fields.Many2one(
        'res.company', related='order_id.company_id', readonly=True)

    @api.multi
    def button_save_data(self):
        return True

    @api.multi
    def button_details(self):
        context = self.env.context.copy()
        context['view_buttons'] = True
        view = {
            'name': _('Details'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.line',
            'view_id': self.env.ref(
                'sale_order_line_form_button.sale_order_line_form_view').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': True,
            'res_id': self.id,
            'context': context
        }
        return view
