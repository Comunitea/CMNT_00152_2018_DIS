# -*- coding: utf-8 -*-

import datetime
import shlex

from odoo import http
from odoo.http import request


class QuoteController(http.Controller):

    @http.route(['/presupuestos', '/presupuestos/presupuesto/<int:id>', ], type='http', auth='public', website=True)
    def quotes(self, add_product=False, delete_product=False, success=False, id=None, search='', **post):
        # Get values to render
        user = request.env.user
        Quote = request.env['sale.quote']
        domain = [('user_id', '=', user.id), ] + request.website.website_domain()
        product_error_msg = None
        product_error_name = None

        # Get and update current quote or create one
        current_quote = Quote.search(domain + [('state', '=', 'current'), ], limit=1)
        if not current_quote and not success:
            vals = {
                'name': 'Solicitud de Presupuesto',
                'date': datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'website_id': request.website.id,
                'user_id': request.env.user.id,
                'contact_phone': request.env.user.phone,
                'contact_email': request.env.user.email,
                'state': 'current',
                'product_ids': None,
            }
            current_quote = Quote.create(vals)
        elif success and current_quote:
            current_quote.product_ids = None

        # Add shop product to current_quote
        if add_product:
            product = request.env['product.template'].search([('id', '=', int(add_product))])
            if product and current_quote and product not in current_quote.product_ids:
                current_quote.product_ids += product
            elif product and current_quote and product in current_quote.product_ids:
                product_error_msg = None
                product_error_name = None
            else:
                product_error_msg = "ERROR! No se ha podido añadir el producto"
                product_error_name = product.name or None

        # Delete shop product from current_quote
        if delete_product:
            product = request.env['product.template'].search([('id', '=', int(delete_product))])
            if product and current_quote and product in current_quote.product_ids:
                current_quote.product_ids = [(3, product.id)]
            elif product and current_quote and product not in current_quote.product_ids:
                product_error_msg = None
                product_error_name = None
            else:
                product_error_msg = "ERROR! No se pudo borrar el producto"
                product_error_name = product.name or None

        # Quotes search
        if search:
            for srch in shlex.split(search):
                domain += ['|', ('name', 'ilike', srch), ]

        # Historical quotes
        quotes = Quote.search(domain + [('state', '=', 'sent'), ], order='date desc')

        # Values to render by default
        values = {'historical_quotes': quotes,  # simulated_products
                  'current_quote': current_quote,
                  'quote_success': success,
                  'product_error_msg': product_error_msg,
                  'product_error_name': product_error_name,
                  'view_quote': False
                  }

        # Values to render a quote
        if id:
            values.update({'current_quote': Quote.search([('id', '=', int(id))]), 'view_quote': True})

        return request.render('website_base.quotes', values)
