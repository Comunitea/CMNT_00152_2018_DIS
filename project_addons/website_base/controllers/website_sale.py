# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time

from odoo import http, _
from odoo.http import request
from odoo.osv.expression import OR
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from werkzeug.exceptions import Unauthorized, NotFound

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row

class WebsiteSale(WebsiteSale):
    
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        order = request.website.sale_get_order()

        if order.locked:
            render_values = self._get_shop_payment_values(order, **post)

            reason_list = []
            if order.risk_lock:
                reason_list.append(_("Risk"))
            if order.unpaid_lock:
                reason_list.append(_("Unpaid"))
            if order.margin_lock:
                reason_list.append(_("Margin"))
            if order.shipping_lock:
                reason_list.append(_("No reach shipping min"))
            if order.amount_lock:
                reason_list.append(_("No reach min amount order"))

            reasons = ", ".join(reason_list)

            errors = [
                _("This order can not be finished becaused is locked"),
                reasons
            ]

            render_values['errors'].append(errors)
            return request.render("website_sale.payment", render_values)

        return super(WebsiteSale, self).payment(**post)

    def _get_customer_products_template_from_customer_prices(self):
        user = request.env.user
        today = time.strftime('%Y-%m-%d')
        
        customer_domain = [('partner_id', '=', user.partner_id.id),
                            '|', ('date_start', '=', False), ('date_start', '<=', today),
                            '|', ('date_end', '=', False), ('date_end', '>=', today),
                            '|', ('product_tmpl_id', '!=', False), ('product_id', '!=', False)]

        customer_products = []
        customer_products += request.env['customer.price'].sudo().search(customer_domain).filtered(lambda x: x.product_tmpl_id != False and \
            x.product_id.website_published).mapped('product_tmpl_id').ids
        customer_products += request.env['customer.price'].sudo().search(customer_domain).filtered(lambda x: x.product_id != False and \
            x.product_id.website_published).mapped('product_id').mapped('product_tmpl_id').ids
        return customer_products


    def _get_search_domain(self, search, category, attrib_values):
        domain = super(WebsiteSale, self)._get_search_domain(search=search, category=category, attrib_values=attrib_values)
        customer_products = False
        if request.env.context.get('customer_prices', False) or not request.env.user.partner_id.show_all_catalogue:

            customer_products = self._get_customer_products_template_from_customer_prices()        

            if len(customer_products) > 0:         
                domain += [('id', 'in', customer_products)]
            else:
                domain += [('id', '=', None)]

        if not request.env.context.get('customer_prices', False) and not request.env.user.partner_id.show_customer_price:
            
            if not customer_products:
                customer_products = self._get_customer_products_template_from_customer_prices()                

            if len(customer_products) > 0:         
                domain += [('id', 'not in', customer_products)]
            
        return domain

    def recalculate_product_list(self, list_type=None, page=0, category=None, search='', ppg=False, **post):
        res = super(WebsiteSale, self).shop(page=page, category=category, search=search, ppg=ppg, **post)

        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        ctx = request.env.context.copy()

        if list_type == 'pricelist':
            url = "/tarifas"
            if category:
                url = "/tarifas/%s" % category
            ctx.update(customer_prices=True)
            request.env.context = ctx

        else:
            url = "/shop"
            if category:
                url = "/shop/%s" % category

        domain = self._get_search_domain(res.qcontext['search'],
                                         res.qcontext['category'],
                                         res.qcontext['attrib_values'])
        
        product = request.env['product.template']
        product_count = product.search_count(domain)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        products = product.sudo().search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

        productAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            selected_products = product.search(domain, limit=False)
            attributes = productAttribute.search([('attribute_line_ids.product_tmpl_id', 'in', selected_products.ids)])
        else:
            attributes = productAttribute.browse(res.qcontext['attributes'].ids)

        res.qcontext.update({
            'products': products,
            'bins': TableCompute().process(products, ppg),
            'attributes': attributes,
            'search_count': product_count,  # common for all searchbox
            'pager': pager,
            'list_type': list_type
        })
        
        return res

    @http.route(['/tarifas'], type='http', auth="public", website=True)
    def customer_prices_shop(self, page=0, category=None, search='', ppg=False, **post):
        return self.recalculate_product_list(list_type='pricelist', page=page, category=category, search=search,
                                             ppg=ppg, **post)
    
    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        if not product:
            raise NotFound() 
        if not request.env.user.partner_id.show_all_catalogue:
            customer_products = self._get_customer_products_template_from_customer_prices()
            if product.id not in customer_products:
                raise Unauthorized(_("You are not authorized to see this product."))
        return super(WebsiteSale, self).product(product=product, category=category, search=search, **kwargs)

    @http.route('/product/<path:path>', type='http', auth="public", website=True)
    def slug_product(self, path, category='', search='', **kwargs):
        res = super(WebsiteSale, self).slug_product(path=path, category=category, search=search, **kwargs)
        if not res.qcontext['product']:
            raise NotFound() 
        if not request.env.user.partner_id.show_all_catalogue and res.qcontext['product']:
            customer_products = self._get_customer_products_template_from_customer_prices()
            if res.qcontext['product'].id not in customer_products:
               raise Unauthorized(_("You are not authorized to see this product.")) 
        return super(WebsiteSale, self).slug_product(path=path, category=category, search=search, **kwargs)