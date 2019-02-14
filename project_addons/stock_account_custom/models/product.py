# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ProductPriceRatio(models.Model):

    _name ="product.price.ratio"

    name = fields.Char('Name')
    purchase_ratio = fields.Float('Purchase ratio', help="Ratio to get reference cost from pricelist_cost")
    sale_ratio = fields.Float('Sale ratio', help="Ratio to get price (list price) from pricelist_cost")

class ProductProduct(models.Model):

    _inherit = 'product.product'

    pricelist_cost = fields.Float(
        'Price list cost', company_dependent=True,
        digits=dp.get_precision('Product cost'),
        groups="stock_account_custom.group_cost_manager", help="Standard price without special purchases")

    reference_cost = fields.Float(
        'Reference cost',
        compute='_compute_reference_cost',
        digits=dp.get_precision('Product cost'),
        help="Cost price for salesman users")

    @api.multi
    def _compute_reference_cost(self):
        for product in self:
            product.reference_cost = product.pricelist_cost * product.product_tmpl_id.cost_ratio_id.purchase_ratio
            print("Calculo coste de referencia para {}: {} €  {} % = {} €".format(product.name, product.pricelist_cost,
                                                                           product.product_tmpl_id.cost_ratio_id.purchase_ratio,  product.reference_cost))

    @api.one
    def _set_cost_method(self):
        if self.property_cost_method == 'fifo' and self.cost_method in ['average', 'standard']:
            old_standard_price = self.standard_price
            ctx = self._context.copy()
            ctx.update(exclude_compute_cost=True)
            pricelist_self = self.width_context(ctx)
            super(ProductProduct, pricelist_self)._set_cost_method()
            if self.standard_price != old_standard_price:
                self.pricelist_cost = self.standard_price
        return super()._set_cost_method()

    @api.multi
    def _compute_stock_value(self):
        return super()._compute_stock_value()
        #
        # ctx = self._context.copy()
        # ctx.update(exclude_compute_cost=True)
        # pricelist_self = self.width_context(ctx)
        # super(ProductProduct, pricelist_self)._compute_stock_value()
        # old_standard_price = self.standard_price

    @api.multi
    def price_compute(self, price_type, uom=False, currency=False, company=False):

        if price_type != 'pricelist_cost':
            return super().price_compute(price_type=price_type, uom=uom, currency=currency, company=company)

        ##COPIA DE price_compute PERO DOY POR HECHO QUE ES PARA reference_cost
        if not uom and self._context.get('uom'):
            uom = self.env['product.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(self._context['currency'])
        products = self.with_context(force_company=company and company.id or self._context.get('force_company',
                                                                                                   self.env.user.company_id.id)).sudo()
        prices = dict.fromkeys(self.ids, 0.0)
        for product in products:
            prices[product.id] = product[price_type] or 0.0
            if uom:
                prices[product.id] = product.uom_id._compute_price(prices[product.id], uom)
            # Convert from current user company currency to asked one
            # This is right cause a field cannot be in more than one currency
            if currency:
                prices[product.id] = product.currency_id.compute(prices[product.id], currency)

        return prices


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    cost_ratio_id = fields.Many2one('product.price.ratio', 'Price ratio', company_dependent=True, help="Product ranking to get reference cost and product price")

    reference_cost = fields.Float(
        'Reference cost', compute='_compute_reference_cost',
        digits=dp.get_precision('Product Price'), groups="stock_account_custom.group_cost_manager", help="Standard price without special purchases")

    pricelist_cost = fields.Float(
        'Pricelist cost', compute='_compute_reference_cost',
        digits=dp.get_precision('Product Price'), groups="stock_account_custom.group_cost_manager", help="Standard price without special purchases")

    @api.depends('product_variant_ids', 'product_variant_ids.reference_cost')
    def _compute_reference_cost(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)

        for template in unique_variants:
            template.reference_cost = template.product_variant_ids.reference_cost
            template.pricelist_cost = template.product_variant_ids.pricelist_cost

        for template in (self - unique_variants):
            n_v = len(template.product_variant_ids)
            pricelist_cost = sum(x.pricelist_cost for x in template.product_variant_ids)
            reference_cost = sum(x.reference_cost for x in template.product_variant_ids)
            template.pricelist_cost = pricelist_cost / n_v
            template.reference_cost = reference_cost / n_v

    @api.multi
    def price_compute(self, price_type, uom=False, currency=False, company=False):

        if price_type != 'pricelist_cost':
            return super().price_compute(price_type=price_type, uom=uom, currency=currency, company=company)

        if not uom and self._context.get('uom'):
            uom = self.env['product.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(self._context['currency'])

        templates = self.with_context(force_company=company and company.id or self._context.get('force_company',
                                                                                                    self.env.user.company_id.id)).sudo()
        prices = dict.fromkeys(self.ids, 0.0)
        for template in templates:
            prices[template.id] = template[price_type] or 0.0
            if uom:
                prices[template.id] = template.uom_id._compute_price(prices[template.id], uom)
            if currency:
                prices[template.id] = template.currency_id.compute(prices[template.id], currency)

        return prices