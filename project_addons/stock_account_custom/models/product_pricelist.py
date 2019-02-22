# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp



class Pricelist(models.Model):
    _inherit = "product.pricelist"

    @api.multi
    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):

        results = super()._compute_price_rule(products_qty_partner=products_qty_partner, date=date, uom_id=uom_id)
        for res in results:
            suitable_rule = results[res][1]
            if suitable_rule.base == 'pricelist_cost':
                product = self.env['product.product'].browse(res)
                tmpl_id = product.product_tmpl_id
                sale_ratio = tmpl_id.cost_ratio_id.sale_ratio
                results[res][0] = sale_ratio
        return results

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(selection_add=[('pricelist_cost', 'Pricelist Cost')], help='Base price for computation.\n'
             'Public Price: The base price will be the Sale/public Price.\n'
             'Cost Price : The base price will be the cost price.\n'
             'Other Pricelist : Computation of the base price based on another Pricelist.\n'
             'Pricelist Cost : The base price will be the pricelist cost.')

    cost_ratio_id = fields.Many2one('product.price.ratio', 'Price ratio', company_dependent=True,
                                    help="Product ranking to get reference cost and product price")