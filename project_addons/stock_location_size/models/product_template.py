# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp

class ProductProduct(models.Model):

    _inherit = 'product.product'
    volume = fields.Float(digits=dp.get_precision('Stock Volume'))


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    volume = fields.Float(digits=dp.get_precision('Stock Volume'))


