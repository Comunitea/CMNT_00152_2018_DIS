# © 2019 Santi Argueso <santi@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
import time


class CustomerPrice(models.Model):
    _inherit = "customer.price"

    price_coef = fields.Float('Margin Coeff', compute="_price_coef",
                              store=True)

    @api.depends('product_id.reference_cost', 'price')
    @api.model
    def _price_coef(self):
        for price_item in self:
            if price_item.product_id:
                if price_item.product_id.reference_cost:
                    price_item.price_coef = price_item.price / \
                                       price_item.product_id.reference_cost
                else:
                    price_item.price_coef = 0
            else:
                price_item.price_coef = 0
