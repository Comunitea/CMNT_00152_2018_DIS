# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    category_id = fields.Many2one(related='product_id.category_id')
    uom_factor = fields.Float(related='product_id.min_sale_unit_id.factor')

    def check_min_sale_unit(self, res):
        #import ipdb; ipdb.set_trace()
        min_sale_unit_id = self.product_id.min_sale_unit_id
        domain = [('category_id', '=', self.product_id.uom_id.category_id.id),
                  ('factor', '<=', min_sale_unit_id.factor)]
        res['domain']['product_uom'] = domain
        product_uom = self.env['product.uom'].search(domain, limit=1, order='factor desc')
        if product_uom:
            self.product_uom = product_uom

        return res

        if min_sale_unit_id.uom_type == 'bigger':
            domain = [('category_id', '=', self.product_id.uom_id.category_id.id), ('factor', '<=', min_sale_unit_id.factor_inv)]
            res['domain']['product_uom'] = domain
            product_uom = self.env['product_uom'].search(domain, limit=1, order='factor desc')
            if product_uom:
                self.product_uom = product_uom

        elif min_sale_unit_id.uom_type == 'smaller':
            domain = [('category_id', '=', self.product_id.uom_id.category_id.id),
                      ('factor', '<=', min_sale_unit_id.factor)]
            res['domain']['product_uom'] = domain

        return res

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id and self.product_id.min_sale_unit_id:
            res = self.check_min_sale_unit(res)
        return res

    # @api.onchange('product_uom_qty')
    # def _onchange_product_uom_qty_bis(self):
    #     super(SaleOrderLine, self)._onchange_product_uom_qty()
    #     if self.product_id and self.product_id.min_sale_unit_id and self.product_uom_qty < self.product_id.min_sale_unit_id.factor_inv:
    #         raise ValidationError(
    #             _('La uni'))


