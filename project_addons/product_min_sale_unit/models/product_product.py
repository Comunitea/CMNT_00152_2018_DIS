# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ProductTemplate(models.Model):

    _inherit = "product.template"

    category_id = fields.Many2one(related="uom_id.category_id", readonly=True)
    min_sale_unit_id = fields.Many2one(
        "uom.uom",
        "Min Sale Unit of Measure",
        required=False,
        domain="[('category_id', '=', category_id)]",
        help="Default Min Sale Unit of Measure used for sale.",
    )
