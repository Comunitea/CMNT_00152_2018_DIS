# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class ProductCustomerInfo(models.Model):
    _inherit = "product.customerinfo"

    @api.multi
    @api.onchange('product_id')
    def onchange_poroduct_id(self):
        for line in self:
            line.product_tmpl_id = line.product_id.product_tmpl_id

class ProductProduct(models.Model):

    _inherit = 'product.product'

    review_order = fields.Boolean() 
   
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    package_qty = fields.Float(
        string='Package Quantity', 
    )
