# © 2019 Santi Argueso <santi@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
import time


class CategoryDiscount(models.Model):
    _name = "category.discount"

    category_id = fields.Many2one('product.category', 'Category', index=1,
                                  required=True)
    partner_id = fields.Many2one('res.partner', 'Customer', required=True,
                                 index=1)
    discount = fields.Float(
        'Discount (%)', default=0.0, digits=dp.get_precision('Product Price'),
        required=True)
    company_id = fields.\
        Many2one('res.company', 'Company',
                 default=lambda self: self.env.user.company_id.id, index=1)

    @api.model
    def get_customer_discount(self, partner_id, category):
        if isinstance(partner_id, (int,)):
            partner = partner_id
        else:
            partner = partner_id.id
        categ = category
        categ_ids = {}
        while categ:
            categ_ids[categ.id] = True
            categ = categ.parent_id
        categ_ids = list(categ_ids)
        domain = [('partner_id', '=', partner),
                  ('category_id', 'in', categ_ids),
                  ]
        customer_discount = self.env['customer.discount'].\
            search(domain, limit=1,order='category_id.parent_left desc')
        if customer_discount:
            return customer_discount
        return False
