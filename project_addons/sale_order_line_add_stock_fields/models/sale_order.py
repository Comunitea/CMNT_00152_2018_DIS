# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _, api
from odoo.addons import decimal_precision as dp

class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.multi
    def get_line_qties(self):
        orders = self.mapped('order_id')
        product_ids = self.mapped('product_id')
        if not product_ids:
            self.write({'virtual_available': 0.00, 'qty_available': 0.00})
            return

        for order in orders:
            to_date = order.requested_date or order.date_order
            qties = product_ids._compute_quantities_dict(self._context.get('lot_id'),
                                                                 self._context.get('owner_id'),
                                                                 self._context.get('package_id'),
                                                                 self._context.get('from_date'),
                                                                 to_date=to_date)

            for line in order.order_line:
                vals = {'virtual_available': qties[line.product_id.id]['virtual_available'],
                         'qty_available': qties[line.product_id.id]['qty_available']}
                line.update(vals)

    qty_available = fields.Float(
        'Quantity On Hand', compute='get_line_qties',
        digits=dp.get_precision('Product Unit of Measure'))
    virtual_available = fields.Float(
        'Forecast Quantity', compute='get_line_qties',
        digits=dp.get_precision('Product Unit of Measure'))

    line_qty_available = fields.Float(
        'Line Quantity Available',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Stock quantity of product at order line create time.\n")

    line_virtual_available = fields.Float(
        'Line Quantity On Hand',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Available quantity of product at order line create time.\n")

    @api.onchange('product_id', 'requested_date', 'date_order')
    def _onchange_for_qties(self):
        return self.get_line_qties()

class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        ctx = self._context.copy()
        for sale in self:
            to_date = fields.Datetime.from_string(sale.requested_date or sale.date_order)
            ctx.update(to_date=to_date)
            for line in sale.with_context(ctx).order_line:
                line.line_qty_available = line.qty_available
                line.line_virtual_available = line.virtual_available
        return super().action_confirm()
