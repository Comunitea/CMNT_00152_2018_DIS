# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time

from odoo import http, _
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute

from werkzeug.exceptions import Unauthorized, NotFound

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class WebsiteSale(WebsiteSale):
    
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        order = request.website.sale_get_order()
        reason_list = []
        # Prevent 500 error page. No buy is possible
        res_check = False

        products_tmpl_on_cart = order.order_line.mapped('product_id').mapped('product_tmpl_id').ids
        order_line_restrictions = request.env['product.customerinfo'].search_read([
            ('name', '=', order.partner_id.id),
            ('product_tmpl_id', 'in', products_tmpl_on_cart)], ['product_tmpl_id', 'min_product_qty'])
        
        if order_line_restrictions:
            for restriction in order_line_restrictions:
                res_check = request.env['sale.order.line'].search([
                    ('product_id.product_tmpl_id', '=', restriction['product_tmpl_id'][0]),
                    ('order_id', '=', order.id),
                    ('product_uom_qty', '<', restriction['min_product_qty'])
                ])
                
                if res_check:
                    reason_list.append(
                        _(("The product {} needs a minimum amount of {} to be shipped.").format(
                            restriction['product_tmpl_id'][1], restriction['min_product_qty']))
                    )

        if order.locked or res_check:
            render_values = self._get_shop_payment_values(order, **post)

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
        customer_products += request.env['customer.price'].sudo().search(customer_domain).filtered(
            lambda x: x.product_tmpl_id is not False and x.product_id.website_published).mapped('product_tmpl_id').ids
        customer_products += request.env['customer.price'].sudo().search(customer_domain).filtered(
            lambda x: x.product_id is not False and x.product_id.website_published).mapped(
            'product_id').mapped('product_tmpl_id').ids
        return customer_products

    def _get_search_domain(self, search, category, attrib_values):
        domain = super(WebsiteSale, self)._get_search_domain(
            search=search, category=category, attrib_values=attrib_values)
        customer_products = False
        if request.env.context.get('customer_prices', False) or not request.env.user.partner_id.show_all_catalogue:

            customer_products = self._get_customer_products_template_from_customer_prices()        

            if len(customer_products) > 0:         
                domain += [('id', 'in', customer_products)]
            else:
                domain += [('id', '=', None)]

        if not request.env.context.get('customer_prices', False) \
                and not request.env.user.partner_id.show_customer_price:
            
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
        context = dict(request.env.context)
        if 'product' not in res.qcontext and 'product_redirect' not in context:
            raise NotFound() 
        if not request.env.user.partner_id.show_all_catalogue and 'product' in res.qcontext:
            customer_products = self._get_customer_products_template_from_customer_prices()
            if res.qcontext['product'].id not in customer_products:
                raise Unauthorized(_("You are not authorized to see this product."))
        return res

    @http.route()
    def payment_confirmation(self, **post):
        order = request.env['sale.order'].sudo().browse(
            request.session.get('sale_last_order_id'))
        if order.need_validation:
            #order.pending_review = True
            # try to validate operation
            reviews = order.request_validation()
            order._validate_tier(reviews)
            if  order._calc_reviews_validated(reviews):
                return super().payment_confirmation(**post)
            else:
                request.website.get_new_cart()
                return request.render("website_base.pending_validation", {'order': order})
        else:
            return super().payment_confirmation(**post)
