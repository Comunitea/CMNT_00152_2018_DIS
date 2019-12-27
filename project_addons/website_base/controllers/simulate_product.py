# -*- coding: utf-8 -*-

import datetime
import shlex

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute

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
                 ], type='http', auth='public', website=True)
    def get_offers(self, page=0, category=None, search='', order='', path='', ppg=False, **post):
        # Catch parent categories for categories menu
        parent_category_ids = []
        if category:
            parent_category_ids = self.get_parent_categories(category)

        # Offers only published, with validate dates and published categories
        Offer = request.env['product.offer']
        current_date = datetime.date.today()
        domain_offers = [('website_published', '=', True), ('end_date', '>=', current_date),
                         ('start_date', '<=', current_date), ] + request.website.website_domain()
        if search:
            for srch in shlex.split(search):
                domain_offers += ['|', '|', ('name', 'ilike', srch), ('subtitle', 'ilike', srch),
                                  ('description', 'ilike', srch), ]
        offers = Offer.search(domain_offers, order=order if order else 'website_sequence desc')
        # Catch not published offer categories if their child are published
        offers = offers.filtered(
            lambda x: x.category_id.website_published if x.category_id.website_published is True or (
                    x.category_id.child_id and x.category_id.child_id.website_published is True) else None)
        # Set is needed to prevent catch the same category on product categories after
        offer_categories = set(offers.mapped('category_id'))
        if category:
            offers = offers.filtered(lambda x: x.category_id.id == int(category))
        bins_table = []
        bins_table += offers

        # Categories for Categories Menu
        Category = request.env['product.public.category']
        domain_category = [('parent_id', '=', False), ('website_published', '=', True), ] \
            + request.website.website_domain()
        all_categories = Category.search(domain_category)

        # Products templates within offer
        Product = request.env['product.template']
        domain_offer_products = [('website_style_ids', '!=', False)]
        if search:
            for srch in shlex.split(search):
                domain_offer_products += ['|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                                          ('description_short', 'ilike', srch), ]
        offer_products = Product.search(domain_offer_products + request.website.website_domain()).filtered(
            lambda x: x if 'oe_ribbon_promo' in x.website_style_ids[0].html_class else None)
        # Catch not published product categories if their child are published
        product_categories = offer_products.mapped('public_categ_ids').filtered(
            lambda x: x.website_published if x.website_published is True or (
                    x.child_id and x.child_id.website_published is True) else None)
        if category:
            offer_products = offer_products.search([('public_categ_ids', 'in', int(category))])

        # Final data
        offer_categories.update(offer_categories, product_categories)
        bins_table += offer_products  # Put offers and products on the same row
        bins = TableCompute().process(bins_table, ppg)
        search_count = len(bins_table)

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
        pager = request.website.pager(url=url_simulated_products, total=search_count, page=page, step=ppg, scope=7, url_args=post)

        # Values to render by default with offer and product list
        values = {'simulated_products': bins_table,  # simulated_products
                  'url_simulated_products': url_simulated_products,
                  'url_simulated_product_templates': url_simulated_product_templates,
                  'categories': all_categories,
                  'category': category,
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

        # Values to render for single offer
        if path:
            offers = request.env['product.offer']
            offer = offers.search([('slug', '=', path)], limit=1)
            if offer:
                values.update({'offer': offer, 'product_category': offer, 'offer_list': False, })
                if not category and offer.category_id:
                    values.update({'category': offer.category_id.id, })
            else:
                return request.env['ir.http'].reroute('/404')

        return request.render('website_base.simulate_product_offer', values)
