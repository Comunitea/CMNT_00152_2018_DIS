# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    category_id = fields.Many2one(related='uom_id.category_id')
    min_sale_unit_id = fields.Many2one('product.uom', 'Min Sale Unit of Measure', required=False,
                                       domain = "[('category_id', '=', category_id)]",
                                       help="Default Min Sale Unit of Measure used for sale.")

    @api.multi
    @api.onchange('product_uom')
    def product_uom_change(self):
        self.min_sale_unit_id = False
        domain = [('category_id', '=', self.product_uom.category_id.id)]
        res['domain']['min_sale_unit_id'] = domain