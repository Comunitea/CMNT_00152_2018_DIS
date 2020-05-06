# -*- coding: utf-8 -*-

from odoo import models, fields, api,  _
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    def dynamic_category_list(self):
        domain = ['|', ('website_ids', '=', False), ('website_ids', 'in', self.id)]
        return self.env['product.public.category'].sudo().search(domain)

    @api.multi
    def _prepare_sale_order_values(self, partner, pricelist):
        values = super()._prepare_sale_order_values(partner, pricelist)
        sale_type = self.env['sale.order.type'].sudo().search([('telesale', '=', True)])
        if sale_type:
            values ['type_id'] = sale_type[0].id
        return values

    @api.multi
    def get_new_cart(self):
        partner = self.env.user.partner_id
        pricelist_id = request.session.get('website_sale_current_pl') or self.get_current_pricelist().id
        if not self._context.get('pricelist'):
            self = self.with_context(pricelist=pricelist_id)

        pricelist = self.env['product.pricelist'].browse(pricelist_id).sudo()
        so_data = self._prepare_sale_order_values(partner, pricelist)
        sale_order = self.env['sale.order'].with_context(force_company=request.website.company_id.id).sudo().create(so_data)

        if sale_order:
            request.session['sale_order_id'] = sale_order.id
            request.session['sale_last_order_id'] = sale_order.id
            sale_order.partner_id.write({'last_website_so_id': sale_order.id})
            return sale_order
        else:
            request.session['sale_order_id'] = None
            request.session['sale_last_order_id'] = None
            request.session['website_sale_current_pl'] = None
            partner.write({'last_website_so_id': None})
            return self.env['sale.order']

    @api.multi
    def _compute_checkout_skip_payment(self):
        for rec in self:
            sale_order = self.env['sale.order'].sudo().browse(request.session['sale_order_id'])
            if sale_order and sale_order.need_validation:
                if request.session.uid:
                    rec.checkout_skip_payment =\
                        request.env.user.partner_id.skip_website_checkout_payment or sale_order.need_validation
            else:
                super()._compute_checkout_skip_payment()


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    dynamic_cat_menu = fields.Boolean(string='Dynamic categories menu', default=False)
