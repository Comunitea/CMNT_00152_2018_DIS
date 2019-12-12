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

    @http.route(['/ofertas', '/ofertas/page/<int:page>', '/ofertas/oferta/<path:path>',
                 ], type='http', auth='public', website=True)
    def get_offers(self, page=0, category=None, search='', order='', path='', ppg=False, **post):
        # Offers
        Offer = request.env['product.offer']
        current_date = datetime.date.today()
        domain_offers = [('website_published', '=', True), ('end_date', '>=', current_date), ] \
            + request.website.website_domain()
        if search:
            for srch in shlex.split(search):
                domain_offers += ['|', '|', ('name', 'ilike', srch), ('subtitle', 'ilike', srch),
                                  ('description', 'ilike', srch), ]
        if category:
            domain_offers += [('category_id', '=', int(category))]
        offers = Offer.search(domain_offers, order=order if order else 'website_sequence desc')
        bins_table = []
        bins_table += offers

        # Categories for Categories Menu
        Category = request.env['product.public.category']
        # TODO: Hide offers with categories unpublished?? Show this categories??
        domain_category = [('website_published', '=', True), ] + request.website.website_domain()
        all_categories = Category.search([('parent_id', '=', False)] + request.website.website_domain())
        offer_categories = Category.search(domain_category).filtered(lambda x: x.offer_ids in offers)

        # Products templates within offers
        Product = request.env['product.template']
        domain_offer_products = [('website_style_ids', '!=', False)]
        offer_products = Product.search(domain_offer_products + request.website.website_domain())
        if offer_products:
            if search:
                for srch in shlex.split(search):
                    domain_offer_products += ['|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                                              ('description_short', 'ilike', srch), ]
            offer_products = offer_products.search(domain_offer_products + request.website.website_domain())
            bins_table += offer_products
        bins = TableCompute().process(bins_table, ppg)
        search_count = len(bins_table)

        # Forms urls for simulated product common templates
        url_simulated_products = "/ofertas"
        url_simulated_product_templates = "/ofertas/oferta/"
        keep = QueryURL(url_simulated_products, search=search, order=order)

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

        # Values to render
        values = {'simulated_products': offers,  # simulated_products
                  'url_simulated_products': url_simulated_products,
                  'simulated_product_templates': offer_products,  # simulated_product_templates
                  'url_simulated_product_templates': url_simulated_product_templates,
                  'all_categories': all_categories,
                  'offer_categories': offer_categories,
                  'search': search,
                  'search_count': search_count,
                  'pager': pager,
                  'bins': bins,
                  'rows': PPR,
                  'keep': keep,
                  'offer_list': True,
                  }

        # For single offer page
        if path:
            offers = request.env['product.offer']
            offer = offers.search([('slug', '=', path)], limit=1)
            if offer:
                values.update({'offer': offer, 'offer_list': False, })
            else:
                return request.env['ir.http'].reroute('/404')

        return request.render('website_base.simulate_product_offer', values)
