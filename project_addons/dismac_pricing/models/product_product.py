# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api
from odoo.tools import pycompat

class ProductProduct(models.Model):
    _inherit = "product.product"

    price_description = fields.Char('Price Explanation',
                                    compute='_compute_product_price', )
    price_coeff = fields.Float('Price Coeff',
                               compute='_compute_price_coeff')

    def _compute_product_price(self):
        """
        When read price, search in customer prices first
        """
        res = super(ProductProduct, self)._compute_product_price()

        partner_id = self._context.get('partner', False)

        qty = self._context.get('quantity', 1.0)
        date = self._context.get('date') or fields.Date.context_today(self)
        if partner_id:
            for product in self:
                pricelist_price = product.price
                pricelist_explanation = "Precio de tarifa "
                # Aplica descuento de categoría
                categ_dis = self.env['category.discount'].\
                    get_customer_discount(partner_id, product.categ_id.id)

                if categ_dis:

                    pricelist_price = pricelist_price * (1- categ_dis[
                        0].discount/100)
                    pricelist_explanation += " . Aplicado descuento de " \
                                             "categoría  " + str(categ_dis[
                        0].discount)

                    # get customet price
                customer_price = self.env['customer.price'].\
                    get_customer_price(partner_id, product, qty) or 0

                #search promotion
                rule = self.env['product.pricelist'].search_promotion(
                    product.id, qty, date)
                if rule:
                    promotion_price = rule.fixed_price
                else:
                    promotion_price = 0

                # Selecciona precio mínimo
                if isinstance(partner_id, pycompat.integer_types):
                    partner = self.env['res.partner'].browse(partner_id)[0]
                else:
                    partner = partner_id
                if partner.fixed_prices:
                    if customer_price:
                        price = customer_price
                        explanation = "Cliente con precios fijos: Precio " \
                                      "pactado "
                    else:
                        price = pricelist_price
                        explanation = "Cliente con precios fijos: Precio " \
                                      "pactado no encontrado. Aplicado " \
                                      "precio de tarifa: \n" + \
                                      pricelist_explanation
                else:
                    price = pricelist_price
                    explanation = pricelist_explanation
                    if customer_price and customer_price < price and price \
                            != 0:
                        price = customer_price
                        explanation = "Encontrado precio pactado por debajo " \
                                      "de tarifa "
                    if promotion_price and promotion_price < price and price \
                            != 0:
                        price = promotion_price
                        explanation = "Aplicada promoción "
                product.price = price
                product.price_description = explanation
            #print(product.price_description)
        return res

    def _compute_price_coeff(self):
        for product in self:
            if product.reference_cost:
                product.price_coeff = product.price / product.reference_cost
            else:
                product.price_coeff = 0
