# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    own_product_codes = fields.Boolean(
        'Own product codes',
        help="If checked, product description is searched in customer code for sale orders")
