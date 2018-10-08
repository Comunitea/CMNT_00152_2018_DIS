# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _, api
from odoo.addons import decimal_precision as dp

class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    qty_available = fields.Float(related='product_id.qty_available')
    virtual_available = fields.Float(related='product_id.virtual_available')
    line_qty_available = fields.Float(
        'Line Quantity Available',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Stock quantity of product at order line create time.\n")

    line_virtual_available = fields.Float(
        'Line Quantity On Hand',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Available quantity of product at order line create time.\n")

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        for order in self:
            if order.product_id:
                order.line_qty_available = order.product_id.qty_available
                order.line_virtual_available = order.product_id.virtual_available
        return res

