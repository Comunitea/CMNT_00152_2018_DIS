# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time

from collections import OrderedDict

from odoo import http, _
from odoo.http import request
from odoo.osv.expression import OR

from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner_id = request.env.user.partner_id

        SaleReport = request.env['sale.order.line']

        history_count = len(SaleReport.read_group([('is_delivery', '=', False), ('order_partner_id', 'child_of', partner_id.id), ('state', 'in', ('sale', 'done'))],
                                                  ['product_uom_qty'], ['product_id', 'order_partner_id']))
        
        review_count = len(request.env.user.review_ids.filtered(lambda x: x.status == 'pending' and x.model == 'sale.order').ids)
        #review_count = len(request.env.user.review_ids.ids)

        values.update({
            'history_count': history_count,
            'review_count': review_count,
        })
        return values

    def _get_my_history_domain(self, filterby):
        domain = []
        user = request.env.user

        partner_id = user.partner_id.id
        ctx = request.env.context.copy()
        
        if 'selected_partner' in ctx:
            partner_id = ctx['selected_partner']
        
        customer_domain = [('order_partner_id', 'child_of', partner_id), ('state', 'in', ('sale', 'done')),
                           ('product_id.type', 'in', ('consu', 'product'))]

        if filterby:
            customer_domain += filterby
        
        customer_products = request.env['sale.order.line'].read_group(customer_domain, ['product_id'],
                                                                  ['product_id', 'order_partner_id'])
        
        if len(customer_products) > 0:
            product_ids = [x['product_id'][0] for x in customer_products] 
            product_tmpl_ids = request.env['product.product'].browse(product_ids).mapped('product_tmpl_id').ids
            domain += [('id', 'in', product_tmpl_ids)]
        else:
            domain = [('id', '=', None)]

        return domain

    @http.route(['/my/history'], type='http', auth="user", website=True)
    def portal_my_history(self, page=1, sortby=None, search=None, search_in='all', filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        product_template = request.env['product.template']

        ctx = request.env.context.copy()
        ctx.update(customer_history=True)

        searchbar_sortings = {
            'ordered_qty': {'label': _('Ordered Qty'), 'order': 'historical_ordered_qty desc'},
            'name': {'label': _('Name'), 'order': 'display_name asc'},
            'order_date': {'label': _('Order Date'), 'order': 'partner_last_order desc'}
        }

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }

        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Search <span class="nolabel"> by name</span>')},
            'default_code': {'input': 'default_code', 'label': _('Search by sku')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        # extends filterby criteria with partner childs
        addresses = partner.child_ids
        for address in addresses:
            searchbar_filters.update({
                str(address.id): {'label': address.name, 'domain': ['|', ('order_id.partner_shipping_id', 'child_of', address.id), ('order_id.partner_id', 'child_of', address.id)]}
            })
            if filterby == str(address.id):
                ctx.update(selected_partner=address.id)

        request.env.context = ctx

        # default filter by value
        if not filterby:
            filterby = 'all'
        domain_filter = searchbar_filters[filterby]['domain']
        domain = self._get_my_history_domain(domain_filter)

        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('default_code', 'all'):
                search_domain = OR([search_domain, [('default_code', 'ilike', search)]])
            domain += search_domain

        # default sortby order
        if not sortby:
            sortby = 'ordered_qty'
        sort_order = searchbar_sortings[sortby]['order']
        
        # count for pager
        order_count = product_template.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/history",
            url_args={'sortby': sortby, 'search_in': search_in, 'search': search, 'filterby': filterby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        products = product_template.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_products_history'] = products.ids[:100]

        # Product links
        keep = QueryURL('/shop', search=search, order=sort_order)

        values.update({
            'products': products.sudo(),
            'page_name': 'products',
            'pager': pager,
            'default_url': '/my/history',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'sortby': sortby,
            'search': search,
            'search_in': search_in,
            'filterby': filterby,
            'keep': keep,
        })
        return request.render("website_base.portal_my_history", values)
    
    @http.route(['/my/reviews', '/my/reviews/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_reviews(self, page=1, sortby=None, date_begin=None, date_end=None, search=None, search_in='all', filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        reviews = request.env.user.review_ids
        
        sale_order_ids = request.env['tier.review'].search([('status', '=', 'pending'), ('model', '=', 'sale.order'), ('id', 'in', reviews.ids)]).mapped('res_id')
        #sale_order_ids = request.env['tier.review'].search([('model', '=', 'sale.order'), ('id', 'in', reviews.ids)]).mapped('res_id')
        SaleOrder = request.env['sale.order']

        domain = [
            ('id', 'in', sale_order_ids)
        ]

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }

        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }

        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Search <span class="nolabel"> by name</span>')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        # extends filterby criteria with partner childs
        addresses = partner.child_ids
        for address in addresses:
            searchbar_filters.update({
                str(address.id): {'label': address.name, 'domain': ['|', ('partner_shipping_id', 'child_of', address.id), ('partner_id', 'child_of', address.id)]}
            })

        # default filter by value
        if not filterby:
            filterby = 'all'

        # adding our filter
            domain += searchbar_filters[filterby]['domain']
        
        # search
        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            domain += search_domain

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('sale.order', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        order_count = SaleOrder.sudo().search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/reviews",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        orders = SaleOrder.sudo().search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_pending_reviews'] = orders.ids[:100]

        # link
        keep = QueryURL('/my/reviews', search=search, order=sort_order)

        values.update({
            'date': date_begin,
            'orders': orders.sudo(),
            'page_name': 'reviews',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/reviews',
            'searchbar_sortings': searchbar_sortings,
            'filterby': filterby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'sortby': sortby,
            'searchbar_inputs': searchbar_inputs,
            'search': search,
            'keep': keep,
            'pending_review': True
        })
        return request.render("sale.portal_my_orders", values)

    @http.route(['/my/reviews/validation'], type='http', auth="user", website=True)
    def portal_review_validation(self, order_id, validation, **kw):

        partner = request.env.user.partner_id
        reviews = request.env.user.review_ids
        review = request.env['tier.review'].search([('model', '=', 'sale.order'), ('id', 'in', reviews.ids), ('res_id', '=', order_id)])
        
        if not review:
            return request.redirect('/my')
        else:
            if validation:
                request.env['sale.order'].sudo().browse(review.res_id).validate_tier()
            else:
                request.env['sale.order'].sudo().browse(review.res_id).reject_tier()
            return request.redirect('/my')     

    @http.route(['/my/reviews/<int:order_id>'], type='http', auth="public", website=True)
    def portal_review_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        res = self.portal_order_page(order_id, report_type, access_token, message, download, **kw)

        res.qcontext.update({
            'pending_review': True,
            'page_name': 'review',
        })

        history = request.session.get('my_pending_reviews', [])
        res.qcontext.update(get_records_pager(history, res.qcontext['sale_order']))     

        return res

    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        res = super(CustomerPortal, self).portal_my_orders(page, date_begin, date_end, sortby, **kw)

        partner = request.env.user.partner_id

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }

        # extends filterby criteria with partner childs
        addresses = partner.child_ids
        for address in addresses:
            searchbar_filters.update({
                str(address.id): {'label': address.name, 'domain': ['|', ('partner_shipping_id', 'child_of', address.id), ('partner_id', 'child_of', address.id)]}
            })

        if not filterby:
            filterby = 'all'

        # If filterby is not 'own' we need to recalculate all the data
        
        if filterby != 'all':
            SaleOrder = request.env['sale.order']

            domain = [
                ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
                ('state', 'in', ['sale', 'done'])
            ]

            searchbar_sortings = {
                'date': {'label': _('Order Date'), 'order': 'date_order desc'},
                'name': {'label': _('Reference'), 'order': 'name'},
                'stage': {'label': _('Stage'), 'order': 'state'},
            }

            # adding our filter
            domain += searchbar_filters[filterby]['domain']

            # default sortby order
            if not sortby:
                sortby = 'date'
            sort_order = searchbar_sortings[sortby]['order']

            archive_groups = self._get_archive_groups('sale.order', domain)
            if date_begin and date_end:
                domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

            # count for pager
            order_count = SaleOrder.search_count(domain)
            # pager
            pager = portal_pager(
                url="/my/orders",
                url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
                total=order_count,
                page=page,
                step=self._items_per_page
            )
            # content according to pager and archive selected
            orders = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
            request.session['my_orders_history'] = orders.ids[:100]

            res.qcontext.update({
                'archive_groups': archive_groups,
                'orders': orders.sudo(),
                'pager': pager,
                'order_count': order_count
            })

        res.qcontext.update({
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })

        return res
        

class WebsiteSaleContext(WebsiteSale):

    def _get_search_domain(self, search, category, attrib_values):
        domain = super()._get_search_domain(search=search, category=category, attrib_values=attrib_values)
        if request.env.context.get('customer_prices', False):
            user = request.env.user
            today = time.strftime('%Y-%m-%d')
            
            customer_domain = [('partner_id', '=', user.partner_id.id),
                               '|', ('date_start', '=', False), ('date_start', '<=', today),
                               '|', ('date_end', '=', False), ('date_end', '>=', today),
                               ('product_tmpl_id', '!=', False)]
        
            customer_products = request.env['customer.price'].sudo().read_group(
                customer_domain, ['product_tmpl_id'], ['product_tmpl_id'])

            if len(customer_products) > 0:         
                product_tmpl_ids = [x['product_tmpl_id'][0] for x in customer_products]   
                domain += [('id', 'in', product_tmpl_ids)]
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
