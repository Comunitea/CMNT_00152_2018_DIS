# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time

from odoo import http, _, fields
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute

from werkzeug.exceptions import Unauthorized, NotFound

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class WebsiteSale(WebsiteSale):
    
    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def address(self, **kw):
        # controlar el cambio de direcciones para cleintes de cartera
        # para que no se pueda hacer (al menos de momento)
        # Se puede plantear otra funcionalidad cambiando esta función
        order = request.website.sale_get_order()
        #if order.partner_id.portfolio:
        #    return request.redirect(kw.get('callback') or '/shop/confirm_order')
        #else:
        return super(WebsiteSale, self).address(**kw)


    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):

        res = super(WebsiteSale, self).payment(**post)

        order = request.website.sale_get_order()
        reason_list = []
        # Prevent 500 error page. No buy is possible
        res_check = False
        errors = False

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
            min_amount_order = order.partner_id.min_amount_order or order.commercial_partner_id.min_amount_order
            if order.risk_lock:
                reason_list.append(_("Por favor consulte con el personal de Dismac con la referencia de pedido: %s para cualquier aclaración" % order.name))
            if order.unpaid_lock:
                reason_list.append(_("Por favor consulte con el personal de Dismac con la referencia de pedido: %s para cualquier aclaración" % order.name))
            if order.margin_lock:
                reason_list.append(_("Por favor consulte con el personal de Dismac con la referencia de pedido: %s " % order.name))
            if order.shipping_lock:
                reason_list.append(_("No alcanza el importe minimo para evitar gastos de envio de %s €" % order.partner_id.min_no_shipping or order.commercial_partner_id.min_no_shipping))
            if order.amount_lock:
                reason_list.append(_("No alcanza el importe mínimo de %s €. Por favor complete el pedido hasta este importe" % min_amount_order))

            reasons = ", ".join(reason_list)
            if not reason_list:
                reasons = _("Unknow")

            errors = [
                _("This order can not be finished because is locked"),
                reasons
            ]

            res.qcontext['errors'].append(errors)

        if errors:
            order.send_lock_alerts(errors)
        return res

    def _get_customer_products_template_from_customer_prices(self):
        user = request.env.user
        today = fields.Date.today()

        customer_domain_pr = [('partner_id', '=', user.partner_id.commercial_partner_id.id),
                            ('product_id', '!=', False),
                           '|',
                            ('date_start', '=', False),
                            ('date_start', '<=', today),
                            '|',
                            ('date_end', '=', False),
                            ('date_end', '>=', today)]
        customer_domain_tmp = [('partner_id', '=', user.partner_id.commercial_partner_id.id),
                            ('product_tmpl_id', '!=', False),
                           '|',
                            ('date_start', '=', False),
                            ('date_start', '<=', today),
                            '|',
                            ('date_end', '=', False),
                            ('date_end', '>=', today)]
        prices_pr = request.env['customer.price'].sudo().search(customer_domain_pr)
        prices_tmp = request.env['customer.price'].sudo().search(customer_domain_tmp)
        customer_products = []
        customer_products += request.env['customer.price'].sudo().search(customer_domain_tmp).mapped('product_tmpl_id').ids
        customer_products += request.env['customer.price'].sudo().search(customer_domain_pr).mapped(
            'product_id').mapped('product_tmpl_id').ids
        return customer_products


    def _get_search_domain(self, search, category, attrib_values):
        domain = request.website.sale_product_domain()
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', ('catalogue_code', '%>', srch), ('name', '%>', srch),
                    ('description_short', 'ilike', srch), ('default_code', '%>', srch)]

        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]

        tag_id = request.env.context.get('tag_id', False)
        if tag_id:
            domain += [('website_published', '=', True), ('tag_ids', 'in', (tag_id))] + \
                      request.env['website'].website_domain()

        customer_products = self._get_customer_products_template_from_customer_prices()
        if request.env.context.get('customer_prices', False) or not request.env.user.partner_id.show_all_catalogue:
            # si estamos consultando la tarifa 
            # O
            # El usuario NO tine marcaddo mostrar todo el catálogo 
            # SOLO ENSEÑA LOS DE TARIFA (ESPCÏFICOS), ESTÉN PUBLICADOS O NO

                    
            
            if len(customer_products) > 0: 
                domain.pop(domain.index(('website_published', '=', True)))       
                domain.insert(0, ('id', 'in', customer_products))
            else:
                domain.insert(0, ('id', '=', None))
            
        elif len(customer_products) > 0:
            #TOdo lo que venga del con el website_published o que sea de tarifa
            domain.insert(0, ('id', 'in', customer_products))
            domain.insert(0, '|')


        # COMENTO ESTO PORQUE NO CREO QUE SEA ASÏ LO ENTIDNO MÁS ANIVE LD EPRECIO , NO DE PROEDTO 
        # if not request.env.context.get('customer_prices', False) \
        #         and not request.env.user.partner_id.show_customer_price:
        #     # SI NO ESTAMOS CONSULTANDO LA TARIFA 
        #     # Y
        #     # el usario NO tiene MOSTRAR PRECIOS PERSONALIZADOS
        #     if not customer_products:
        #         customer_products = self._get_customer_products_template_from_customer_prices()                

        #     if len(customer_products) > 0:         
        #         domain += [('id', 'not in', customer_products)]
        print(domain)
        return domain


    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        res = super(WebsiteSale, self)._get_search_order(post)
        print(post)
        search = post.get('search', False)
        if search:
            order = "("
            ini_str = True
            for srch in search.split(" "):
                if ini_str == False:
                    order += " + "
                order += "coalesce(word_similarity(product_template.catalogue_code, '%s'),0)  +coalesce(word_similarity(product_template.name, '%s'), 0) \
                            + coalesce(word_similarity(product_template.description_short, '%s'), 0)  +coalesce(word_similarity(product_template.default_code, '%s'), 0)" % (srch, srch, srch, srch)
                ini_str= False
            order += ") DESC"
            print(order)
            return order
        print ("ORDEN NORMAL !!!!!!!!!!!!!!!!!!!!!")
        print(post)
        return '%s ,description_short desc, id desc' % post.get('order', 'website_sequence desc')

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

        
        order = self._get_search_order(post)

        products = product.sudo().search(domain, limit=ppg, offset=pager['offset'], order=order)

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

    @http.route(['/tarifas', '/tarifas/page/<int:page>'], type='http', auth="public", website=True)
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
        order = request.env['sale.order'].sudo().browse(request.session.get('sale_last_order_id'))

        if order.partner_id.external_review or order.commercial_partner_id.external_review:
            # Para pedidos USC , se hace revisión exernal
            request.website.get_new_cart()
            order.write({'state': 'sent'})
            return request.render("website_base.external_pending_validation", {'order': order})
        else: 
            if order.need_validation:
                # try to validate operation
                reviews = order.request_validation()
                order._validate_tier(reviews)
                if order._calc_reviews_validated(reviews):
                    return super().payment_confirmation(**post)
                else:
                    request.website.get_new_cart()
                    return request.render("website_base.pending_validation", {'order': order})
            else:
                return super().payment_confirmation(**post)
