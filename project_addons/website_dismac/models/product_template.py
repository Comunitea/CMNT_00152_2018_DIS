# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_product_historical_ordered_qty(self, user):

        customer_domain = [('partner_id', '=', user.partner_id.id), ('state', '=', 'sale'), ('product_tmpl_id', '=', self.id)]
        
        customer_product_data = self.env['sale.report'].sudo().read_group(customer_domain, ['product_uom_qty'], ['product_tmpl_id', 'partner_id'])

        return customer_product_data[0]['product_uom_qty']
        

