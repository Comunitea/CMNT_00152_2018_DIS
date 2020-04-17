# -*- coding: utf-8 -*-

from odoo import models, fields, api,  _


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

class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    dynamic_cat_menu = fields.Boolean(string='Dynamic categories menu', default=False)
