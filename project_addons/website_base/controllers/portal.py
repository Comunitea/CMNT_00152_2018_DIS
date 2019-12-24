# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
import io
import time
from werkzeug.utils import redirect

from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        SaleReport = request.env['sale.report']
        history_count = SaleReport.search_count([
            ('partner_id', '=', partner.id), ('state', '=', 'sale')
        ])

        values.update({
            'history_count': history_count,
        })
        return values


    def _get_my_history_domain(self):
        domain = []
        user = request.env.user
        
        customer_domain = [('partner_id', '=', user.partner_id.id), ('state', '=', 'sale')]
    
        customer_products = request.env['sale.report'].sudo().read_group(customer_domain, ['product_tmpl_id'], ['product_tmpl_id', 'partner_id'])
        if len(customer_products) > 0:         
            product_tmpl_ids = [x['product_tmpl_id'][0] for x in customer_products]  
            domain +=[('id', 'in', product_tmpl_ids)]
        else:
            domain = [('id', '=', None)]

        return domain

    @http.route(['/my/history'], type='http', auth="user", website=True)
    def portal_my_history(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        product_template = request.env['product.template']

        ctx = request.env.context.copy()
        ctx.update(customer_history=True)
        request.env.context= ctx

        domain = self._get_my_history_domain()

        searchbar_sortings = {
            'ordered_qty': {'ordered_qty': _('Ordered Qty'), 'order': 'historical_ordered_qty desc'},
            'name': {'label': _('Reference'), 'order': 'display_name'}
        }
        # default sortby order
        if not sortby:
            sortby = 'ordered_qty'
        sort_order = searchbar_sortings[sortby]['order']

        # count for pager
        order_count = product_template.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/history",
            url_args={'sortby': sortby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        products = product_template.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_products_history'] = products.ids[:100]

        values.update({
            'products': products.sudo(),
            'page_name': 'products',
            'pager': pager,
            'default_url': '/my/history',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("website_base.portal_my_history", values)
        


class WebsiteSaleContext(WebsiteSale):


    def _get_search_domain(self, search, category, attrib_values):
        domain = super()._get_search_domain (search=search, category=category, attrib_values=attrib_values)
        if request.env.context.get('customer_prices', False):
            user = request.env.user
            today = time.strftime('%Y-%m-%d')
            
            customer_domain = [('partner_id', '=', user.partner_id.id),
                '|', ('date_start', '=', False), ('date_start', '<=', today),
                '|', ('date_end', '=', False), ('date_end', '>=', today),
                ('product_tmpl_id', '!=', False)]
        
            customer_products = request.env['customer.price'].sudo().read_group(customer_domain, ['product_tmpl_id'], ['product_tmpl_id'])
            if len(customer_products) > 0:         
                product_tmpl_ids = [x['product_tmpl_id'][0] for x in customer_products]   
                domain +=[('id', 'in', product_tmpl_ids)]
            else:
                domain = [('id', '=', None)]

        return domain
    

    def recalculate_product_list(self, list_type=None, page=0, category=None, search='', ppg=False, **post):
        res = super(WebsiteSaleContext, self).shop(page=page, category=category, search=search, ppg=ppg, **post)

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
            request.env.context= ctx

        else:
            url = "/shop"
            if category:
                url = "/shop/%s" % category

        domain = self._get_search_domain(res.qcontext['search'], res.qcontext['category'], res.qcontext['attrib_values'])
        
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


    @http.route([
        '/tarifas'
    ], type='http', auth="public", website=True)
    def customer_prices_shop(self, page=0, category=None, search='', ppg=False, **post):
        return self.recalculate_product_list(list_type='pricelist', page=page, category=category, search=search, ppg=ppg, **post)