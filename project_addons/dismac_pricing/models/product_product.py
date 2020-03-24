# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models
from odoo.tools import pycompat


class ProductProduct(models.Model):
    _inherit = "product.product"

    price_description = fields.Char(
        "Price Explanation", compute="_compute_product_price"
    )
    price_coeff = fields.Float("Price Coeff", compute="_compute_price_coeff")


    def _get_price_and_discount(self, qty, partner_id, date):
        res = {
                'price': 0,
                'discount': 0,
                'explanation': ''
                }
        discount = 0
        pricelist_price = pricelist_price_discount = self.price
        pricelist_explanation = "Precio de tarifa "

        # SE cpopia toda esta parte par mostrar el descuetno de forma explícita
        # PEro se necesita en esta parte para poder comprar precios incluido el descuento
        # Aplica descuento de categoría
        categ_dis = self.env["category.discount"].get_customer_discount(
                partner_id, self.categ_id.id
        )

        if categ_dis:

            pricelist_price_discount = pricelist_price * (
                1 - categ_dis[0].discount / 100
            )
            pricelist_explanation += (
                " . Encontraro descuento de "
                    "categoría  " + str(categ_dis[0].discount)
            )
            discount = categ_dis[0].discount

            # get customet price
        customer_price = (
            self.env["customer.price"].get_customer_price(
                partner_id, self, qty
            )
            or 0
        )

        # search promotion
        rule = self.env["product.pricelist"].search_promotion(
            self.id, qty, date
        )
        if rule:
            promotion_price = rule.fixed_price
        else:
            promotion_price = 0

        # Selecciona precio mínimo
        if isinstance(partner_id, pycompat.integer_types):
            partner = self.env["res.partner"].browse(partner_id)[0]
        else:
            partner = partner_id
        if partner.fixed_prices:
            discount = 0
            if customer_price:
                price = customer_price
                explanation = (
                    "Cliente con precios fijos: Precio " "pactado "
                )
            else:
                price = pricelist_price
                explanation = (
                    "Cliente con precios fijos: Precio "
                    "pactado no encontrado. Aplicado "
                    "precio de tarifa: \n" + pricelist_explanation
                )
        else:
            price = pricelist_price
            explanation = pricelist_explanation
            if customer_price and customer_price < pricelist_price_discount and pricelist_price_discount != 0:
                price = customer_price
                explanation = (
                    "Encontrado precio pactado por debajo " "de tarifa "
                )
                discount = 0
            if (
                promotion_price
                and promotion_price < pricelist_price_discount
                and promotion_price < price
                and price != 0
            ):
                price = promotion_price
                explanation = "Aplicada promoción "
                discount = 0
                
        res['price'] = price
        res['discount'] = discount
        res['explanation'] += explanation
        return res


    def _compute_product_price(self):
        """
        When read price, search in customer prices first
        """
        res = super(ProductProduct, self)._compute_product_price()

        partner_id = self._context.get("partner", False)

        qty = self._context.get("quantity", 1.0)
        date = self._context.get("date") or fields.Date.context_today(self)
        if partner_id:
            for product in self:
                price_and_discount = product._get_price_and_discount (qty, partner_id, date)
                product.price = price_and_discount['price']
                product.price_description = price_and_discount['explanation']
        return res

    def _compute_price_coeff(self):
        for product in self:
            if product.reference_cost:
                product.price_coeff = product.price / product.reference_cost
            else:
                product.price_coeff = 0
