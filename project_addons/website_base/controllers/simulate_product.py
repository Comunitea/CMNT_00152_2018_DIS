# -*- coding: utf-8 -*-

import datetime
import shlex

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute

from werkzeug.exceptions import NotFound

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
    def get_offers(self, page=1, category=None, search='', order='', path='', slug=False, ppg=False, **post):
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

        # SQL initial statements
        bins_table = []
        sql_select_offers = "select po.id, po.name AS name, 'Offer' AS type from product_offer po \
            JOIN product_public_category ppc ON po.category_id = ppc.id \
            where po.website_published = True \
            and (po.end_date >= NOW() OR po.end_date IS NULL) \
            and po.start_date <= NOW() \
            AND ppc.website_published = True \
            AND (po.website_id IS NULL OR po.website_id = {}) \
            AND (ppc.parent_id IS NULL OR ppc.parent_id IN \
             (SELECT id from product_public_category WHERE website_published = True))".format(request.website.id)

        sql_select_products = "select pt.id, pt.name AS name, 'Product' AS type from product_template pt \
            where pt.id IN ( \
                select product_template_id \
                from product_style_product_template_rel pspt \
                JOIN product_style ps ON  pspt.product_style_id = ps.id \
                WHERE ps.html_class = 'oe_ribbon_promo' \
            ) \
            and pt.active = True \
            AND (pt.website_id IS NULL OR pt.website_id = {})".format(request.website.id)

        # Offers only published, with validate dates and published categories
        Offer = request.env['product.offer']
        current_date = datetime.date.today()
        domain_offers = [('website_published', '=', True), ('end_date', '>=', current_date),
                         ('start_date', '<=', current_date), ] + request.website.website_domain()
        if search:
            for srch in shlex.split(search):
                domain_offers += ['|', '|', ('name', 'ilike', srch), ('description_short', 'ilike', srch),
                                  ('description_full', 'ilike', srch), ]
                # Adding the search filters to the sql statement
                sql_select_offers += "and (po.name ilike '%{}%' OR po.description_short ilike '%{}%' \
                    OR po.description_full ilike '%{}%')".format(srch, srch, srch)

        offers = Offer.search(domain_offers, order=order if order else 'website_sequence desc')
        # Catch not published offer categories if their child are published
        offers = offers.filtered(
            lambda x: x.category_id.website_published if x.category_id.website_published is True or (
                    x.category_id.child_id and x.category_id.child_id.website_published is True) else None)
        # Set is needed to prevent catch the same category on product categories after
        offer_categories = set(offers.mapped('category_id'))
        if public_category:
            offers = offers.filtered(lambda x: x.category_id.id == public_category.id)
            # Adding the category filter to the sql statement
            sql_select_offers += "AND ppc.id = {}".format(public_category.id)

        # Categories for Categories Menu
        Category = request.env['product.public.category']
        domain_category = [('parent_id', '=', False), ('website_published', '=', True), ] \
            + request.website.website_domain()
        all_categories = Category.search(domain_category)

        # Products templates within offer
        Product = request.env['product.template']
        domain_offer_products = [('website_style_ids', '!=', False), ] + request.website.website_domain()
        if search:
            for srch in shlex.split(search):
                domain_offer_products += ['|', '|', ('name', 'ilike', srch), ('description_short', 'ilike', srch),
                                          ('description_full', 'ilike', srch), ]
                # Adding the search filters to the sql statement
                sql_select_products += "and (pt.name ilike '%{}%' OR pt.description_short ilike '%{}%' \
                    OR pt.description_full ilike '%{}%')".format(srch, srch, srch)
        offer_products = Product.search(domain_offer_products).filtered(
            lambda x: x if 'oe_ribbon_promo' in x.website_style_ids[0].html_class else None)
        # Catch not published product categories if their child are published
        product_categories = offer_products.mapped('public_categ_ids').filtered(lambda x: x.website_published)
        if public_category:
            offer_products = offer_products.search([('public_categ_ids', 'in', public_category.id)])
            # Adding the category filter to the sql statement
            sql_select_products += "AND pt.id IN ( \
                select product_template_id \
                from product_public_category_product_template_rel \
                where product_public_category_id = {} \
            )".format(public_category.id)

        # Forms urls for simulated product common templates
        url_simulated_products = "/ofertas"
        url_simulated_product_templates = "/ofertas/oferta/"
        keep = QueryURL('/shop', search=search, order=order)

        #SQL COUNT EXECUTE
        sql_select_union = "{} UNION {}".format(sql_select_offers, sql_select_products)
        if order != '':
            sql_select_union += " ORDER BY {}".format(order)
        count_select = "SELECT COUNT(*) FROM ({}) x".format(sql_select_union)
        request.cr.execute(count_select)
        search_count = request.cr.fetchone()[0]

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
            offset = (page-1)*PPG            

        pager = request.website.pager(url=url_simulated_products, total=search_count, page=page,
                                      step=ppg, scope=7, url_args=post)
        
        #Final SQL EXECUTE
        final_sql_statement = "{} LIMIT {}".format(sql_select_union, PPG)
        if offset:
            final_sql_statement += " OFFSET {}".format(offset)

        request.cr.execute(final_sql_statement)
        sql_result = request.cr.fetchall()

        offer_list = []
        product_list = []

        for element in sql_result:
            if 'Offer' in element:
                offer_list.append(element[0])
            else:
                product_list.append(element[0])
    
        bins_table += Offer.search([('id', 'in', offer_list)])
        bins_table += Product.search([('id', 'in', product_list)])

        # Final data
        offer_categories.update(offer_categories, product_categories)
        bins = TableCompute().process(bins_table, ppg)
        search_count = len(bins_table)

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
                    values.update({'category': offer.category_id })
            else:
                return request.env['ir.http'].reroute('/404')

        return request.render('website_base.simulate_product_offer', values)
