# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductProduct(models.Model):

    _inherit = 'product.product'

    review_order = fields.Boolean() 
   
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    package_qty = fields.Float(
        string='Package Quantity', 
    )
