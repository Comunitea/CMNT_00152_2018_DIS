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


    real_stock_cost = fields.Float('Real stock cost',
                                   compute="_get_compute_custom_costs",
                                   digits=dp.get_precision('Product cost'),
                                   groups="stock_account_custom.group_cost_manager",
                                   help="Stock value / Qty")
    real_stock_cost_fixed = fields.Float('Fixed real stock cost',
                                   compute="_get_compute_custom_costs",
                                   digits=dp.get_precision('Product cost'),
                                   groups="stock_account_custom.group_cost_manager",
                                   help="Stock value / Qty (without special purchases)")
    pricelist_cost = fields.Float('Price list cost',
                                   digits=dp.get_precision('Product cost'),
                                   groups="stock_account_custom.group_cost_manager",
                                   help="Cost price used in pricelist (Fixed real stock cost manually frozen")
    reference_cost = fields.Float('Reference cost',
                                  compute="_get_compute_custom_costs",
                                   digits=dp.get_precision('Product cost'),
                                   help="Cost price for salesman users (Fixed real stock cost fixed by ratio)")

    def _get_compute_custom_costs_with_context(self, ctx):
        qty_at_date = self.qty_at_date
        product = self.with_context(ctx)
        candidates = product._get_fifo_candidates_in_move()
        qty_remaining = sum(x.remaining_qty for x in candidates)
        qty = qty_at_date - qty_remaining
        return product.stock_value / qty

    @api.multi
    def _get_compute_custom_costs(self):
        ## Real stock_cost: Todos los movimientos
        for product in self:
            product.real_stock_cost = product.stock_value / product.qty_at_date
        ## Fixed real stock_cost: Solo los movimientos con exclude_compute_cost = False
        ctx = self._context.copy()
        ctx.update(exclude_compute_cost=True)
        for product in self:
            product.real_stock_cost_fixed = product._get_compute_custom_costs_with_context(ctx)
            if product.product_tmpl_id.cost_ratio_id:
                product.reference_cost = product.real_stock_cost_fixed * product.product_tmpl_id.cost_ratio_id.purchase_ratio or 1.0
            else:
                product.reference_cost = product.real_stock_cost_fixed

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


    stock_value = fields.Float(
        'Value', compute='_compute_reference_cost')
    qty_at_date = fields.Float(
        'Quantity', compute='_compute_reference_cost')
    reference_cost = fields.Float(
        'Reference cost', compute='_compute_reference_cost',
        digits=dp.get_precision('Product Price'), groups="stock_account_custom.group_cost_manager", help="Cost price for salesman users (Fixed real stock cost fixed by ratio)")
    pricelist_cost = fields.Float(
        'Pricelist cost',
        digits=dp.get_precision('Product Price'), groups="stock_account_custom.group_cost_manager", help="Cost price used in pricelist (Fixed real stock cost manually frozen")
    real_stock_cost = fields.Float(
        'Real stock cost', compute='_compute_reference_cost',
        digits=dp.get_precision('Product Price'), groups="stock_account_custom.group_cost_manager",
        help="Stock value / Qty")
    real_stock_cost_fixed = fields.Float(
        'Fixed real stock cost', compute='_compute_reference_cost',
        digits=dp.get_precision('Product Price'), groups="stock_account_custom.group_cost_manager",
        help="Stock value / Qty (without special purchases)")


    @api.depends('product_variant_ids', 'product_variant_ids.reference_cost')
    def _compute_reference_cost(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)

        for template in unique_variants:
            template.reference_cost = template.product_variant_ids.reference_cost
            template.pricelist_cost = template.product_variant_ids.pricelist_cost
            template.real_stock_cost = template.product_variant_ids.real_stock_cost
            template.real_stock_cost_fixed = template.product_variant_ids.real_stock_cost_fixed

            template.stock_value = template.product_variant_ids.stock_value
            template.qty_at_date = template.product_variant_ids.qty_at_date

        for template in (self - unique_variants):
            n_v = len(template.product_variant_ids) or 1
            pricelist_cost = sum(x.pricelist_cost for x in template.product_variant_ids)
            reference_cost = sum(x.reference_cost for x in template.product_variant_ids)
            real_stock_cost = sum(x.real_stock_cost for x in template.product_variant_ids)
            real_stock_cost_fixed = sum(x.fixed_real_stock_cost for x in template.product_variant_ids)
            stock_value = sum(x.stock_value for x in template.product_variant_ids)
            qty_at_date = sum(x.qty_at_date for x in template.product_variant_ids)

            template.pricelist_cost = pricelist_cost / n_v
            template.reference_cost = reference_cost / n_v
            template.real_stock_cost = real_stock_cost / n_v
            template.real_stock_cost_fixed = real_stock_cost_fixed / n_v
            template.stock_value = stock_value / n_v
            template.qty_at_date = qty_at_date / n_v

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