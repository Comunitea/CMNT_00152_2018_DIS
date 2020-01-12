# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    def get_line_qties(self):
        for line in self:
            if not line.product_id:
                line.write({"virtual_available": 0.00, "qty_available": 0.00})
                continue

            ctx = self._context.copy()
            ctx.update(location=line.order_id.warehouse_id.lot_stock_id.id)
            qties = line.product_id.with_context(ctx)._compute_quantities_dict(lot_id=False,owner_id=False,package_id=False, to_date=line.order_id.expected_date)
            if line.state in ('done', 'sale'):
                qty_enough = line.line_virtual_available >= line.product_uom_qty
            else:
                qty_enough = qties[line.product_id.id][
                    "virtual_available"
                ] >= line.product_uom_qty
            vals = {
                'qty_enough': qty_enough,
                "virtual_available": qties[line.product_id.id]["virtual_available"],
                "qty_available": qties[line.product_id.id]["qty_available"]
            }
            if qties[line.product_id.id]["virtual_available"] == qties[line.product_id.id]["qty_available"]:
                stock_str = '{}'.format(qties[line.product_id.id]["qty_available"])
            else:
                stock_str = '{} / {}'.format(qties[line.product_id.id]["virtual_available"], qties[line.product_id.id]["qty_available"])
            vals.update(stock_str = stock_str)
            line.update(vals)

    qty_enough = fields.Boolean('Qty enough', compute="get_line_qties")
    stock_str = fields.Char('Disponible/Total',
        compute="get_line_qties")
    qty_available = fields.Float(
        "Quantity On Hand",
        compute="get_line_qties",
        digits=dp.get_precision("Product Unit of Measure"),
    )
    virtual_available = fields.Float(
        "Forecast Quantity",
        compute="get_line_qties",
        digits=dp.get_precision("Product Unit of Measure"),
    )

    line_stock_str = fields.Char('Disponible/Total')
    line_qty_available = fields.Float(
        "Line Quantity Available",
        digits=dp.get_precision("Product Unit of Measure"),
        help="Stock quantity of product at order line create time.\n",
    )
    line_virtual_available = fields.Float(
        "Line Quantity On Hand",
        digits=dp.get_precision("Product Unit of Measure"),
        help="Available quantity of product at order line create time.\n",
    )


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        ctx = self._context.copy()
        for sale in self:
            to_date = fields.Datetime.from_string(
                sale.commitment_date or sale.date_order
            )
            ctx.update(to_date=to_date)
            for line in sale.with_context(ctx).order_line:
                line.line_stock_str = line.stock_str
                line.line_qty_available = line.qty_available
                line.line_virtual_available = line.virtual_available
        return super().action_confirm()
