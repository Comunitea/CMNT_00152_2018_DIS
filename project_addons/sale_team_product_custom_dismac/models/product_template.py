# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from pprint import pprint

class ProductTemplate(models.Model):
    _inherit = "product.template"

    sale_team_product_ids = fields.One2many('sale.team.product', 'product_tmpl_id', String="Sale team product data")