# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    property_stock_location = fields.Many2one(
        'stock.location', 'Stock location',
        company_dependent=True,
        domain=[('usage', 'like', 'internal')],
        help="This stock location will be used, as the destination location for stock moves generated by purchase orders.")


class ProductCategory(models.Model):

    _inherit = 'product.category'

    property_stock_location = fields.Many2one(
        'stock.location', 'Stock location',
        company_dependent=True,
        domain=[('usage', 'like', 'internal')],
        help="This stock location will be used, as the destination location for stock moves generated by purchase orders for this category.")
