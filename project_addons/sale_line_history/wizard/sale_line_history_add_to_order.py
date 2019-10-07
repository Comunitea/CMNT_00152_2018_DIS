# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models
import odoo.addons.decimal_precision as dp


class SaleOrderLineHistoryAddToOrder(models.TransientModel):
    _name = 'sale.order.line.history.add.to.order'

    qty = fields.Float(digits=dp.get_precision('Product Unit of Measure'))

    def add_to_order(self):
        original_line_id = self._context.get('active_id')
        original_line = self.env['sale.order.line'].browse(original_line_id)
        line_values = {'product_id': original_line.product_id.id,
                       'order_id': self._context.get('order_id'),
                       'product_uom_qty': self.qty}
        vals = self.env['sale.order.line'].play_onchanges(
            line_values, ['product_id', 'product_uom_qty'])
        self.env['sale.order.line'].create(vals)