# -*- coding: utf-8 -*-

import datetime
import shlex

from odoo import http, _
from odoo.http import request
from odoo.osv import expression

from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute

from werkzeug.exceptions import NotFound, Unauthorized

# TODO: Change this by settings
PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class SimulateProductController(http.Controller):

    def get_parent_categories(self, category):
        Category = request.env['product.public.category']
        new_category = Category.search([('id', '=', int(category))])
        parent_category_ids = [new_category.id]
        current_category = new_category
        while current_category.parent_id:
            parent_category_ids.append(current_category.parent_id.id)
            current_category = current_category.parent_id
        return parent_category_ids

    @http.route(['/ofertas', '/ofertas/page/<int:page>', '/ofertas/oferta/<path:path>',
                 '/ofertas/category/<path:slug>', '/ofertas/category/<path:slug>/page/<int:page>',
                 '''/ofertas/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>''',
                 '''/ofertas/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>/page/<int:page>'''
                 ], type='http', auth='public', website=True)
    def get_offers(self, page=1, category=None, search='', order='', path=None, slug=False, ppg=False, **post):
        offset = False
        # Catch category by slug(category) or category.slug
        domain = [('id', 'in', [])]
        if slug:
            domain = [('slug', '=', slug)]
        if category:
            domain = [('id', '=', int(category))]
        public_category = request.env['product.public.category'].search(domain, limit=1)
        parent_category_ids = self.get_parent_categories(public_category)
        if (slug or category) and (not public_category or not public_category.can_access_from_current_website()):
            raise NotFound()

        bins_table = []

        # Offers only published, with validate dates and published categories
        Offer = request.env['report.website.offer']
        current_date = datetime.date.today()
        domain_offers = request.website.website_domain() + [('start_date', '<=', current_date)]
        domain_offers = expression.OR([domain_offers, [('odoo_model', '=', 'product.template'),
                                                       ('start_date', '=', False)]])
        domain_offers = expression.AND([domain_offers, ['|', ('end_date', '>=', current_date),
                                                        ('end_date', '=', False)]])
        if public_category:
            domain_offers += [('product_public_category_id', '=', public_category.id)]
        if search:
            for srch in shlex.split(search):
                domain_offers += ['|', '|', ('name', 'ilike', srch), ('description_short', 'ilike', srch),
                                  ('description_full', 'ilike', srch), ]
        
        search_count = Offer.search_count(domain_offers)
        offers = Offer.search(domain_offers, order=order)

        # Set is needed to prevent catch the same category on product categories after
        offer_categories = set(offers.mapped('product_public_category_id'))

        # Categories for Categories Menu
        Category = request.env['product.public.category']
        domain_category = [('parent_id', '=', False), ('website_published', '=', True), ] \
            + request.website.website_domain()
        all_categories = Category.search(domain_category)

        # Forms urls for simulated product common templates
        url_simulated_products = "/ofertas"
        url_simulated_product_templates = "/ofertas/oferta/"
        keep = QueryURL('/shop', search=search, order=order)

        # Pager
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
        
        if page != 1:
            offset = (int(page)-1)*PPG

        if order != '':
            post['order'] = order

        if search != '':
            post['search'] = search

        pager = request.website.pager(url=url_simulated_products, total=search_count, page=page,
                                      step=ppg, scope=7, url_args=post)

        offers = Offer.search(domain_offers, order=order, limit=PPG, offset=offset)

        for offer in offers:
            
            if offer['odoo_model'] == 'product.offer':
                bins_table.append(request.env['product.offer'].search([('id', '=', int(offer['model_id']))]))
            elif offer['odoo_model'] == 'product.template':
                bins_table.append(request.env['product.template'].search([('id', '=', int(offer['model_id']))]))

        # Final data
        bins = TableCompute().process(bins_table, ppg)

        # Values to render by default with offer and product list
        values = {'simulated_products': bins_table,  # simulated_products
                  'url_simulated_products': url_simulated_products,
                  'url_simulated_product_templates': url_simulated_product_templates,
                  'categories': all_categories,
                  'category': public_category,
                  'offer_categories': offer_categories,
                  'search': search,
                  'search_count': search_count,
                  'pager': pager,
                  'bins': bins,
                  'rows': PPR,
                  'keep': keep,
                  'offer_list': True,
                  'parent_category_ids': parent_category_ids,
                  }

        if public_category:
            values['main_object'] = public_category

        # Values to render for single offer
        if path:
            offers = request.env['product.offer']
            offer = offers.search([('slug', '=', path)], limit=1)
            if offer:
                values.update({'main_object': offer, 'offer': offer, 'product_category': offer, 'offer_list': False, })
                if not public_category and offer.category_id:
                    values.update({'category': offer.category_id})
            else:
                return request.env['ir.http'].reroute('/404')
        return request.render('website_base.simulate_product_offer', values)
