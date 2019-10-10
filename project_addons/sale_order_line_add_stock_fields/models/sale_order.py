# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    line_qty_available = fields.Float(
        'Line Quantity Available',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Stock quantity of product at order line create time.\n")

    line_virtual_available = fields.Float(
        'Line Quantity On Hand',
        digits=dp.get_precision('Product Unit of Measure'),
        help="Available quantity of product at order line create time.\n")


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        ctx = self._context.copy()
        for sale in self:
            to_date = fields.Datetime.from_string(sale.commitment_date or sale.date_order)
            ctx.update(to_date=to_date)
            for line in sale.with_context(ctx).order_line:
                line.line_qty_available = line.qty_available
                line.line_virtual_available = line.virtual_available
        return super().action_confirm()
