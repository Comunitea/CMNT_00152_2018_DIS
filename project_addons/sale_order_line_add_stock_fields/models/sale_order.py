# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):

    _inherit = "sale.order"


    @api.multi
    def _get_default_location_src_id(self):
        return self.warehouse_id.lot_stock_id

    default_location_src_id = fields.Many2one('stock.location', 'Ubicación de salida', default=_get_default_location_src_id,
                                              readonly=True,
                                              states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    def get_line_qties(self):
        # if len(self)>40 and False:
        #     params = self._context.get('params', False)
        #     if params:
        #         id = params.get('id', False)
        #         ids = params.get('active_ids', False)
        #
        #         if params.get('model', False) == 'sale.order' and id or ids:
        #             self = self.filtered(lambda x:(ids and x.order_id.id in ids) or (id and x.order_id.id == id) )
        #         if params.get('model', False) == 'sale.order.line' and id or ids:
        #             self = self.filtered(lambda x:(ids and x.id in ids) or (id and x.id == id))
        #
        #     #import pdb; pdb.set_trace()

        #print ("Entro en get_line_qties con {} y contexto {}".format(len(self), self._context))
        ctx = self._context.copy()
        for so in self.with_prefetch().mapped('order_id') :
            ctx.update(exclude_sale_line_id=so.order_line.ids,
                       location=so.warehouse_id.lot_stock_id.id)
            for line in so.with_context(ctx).order_line.filtered(lambda x: x.product_id):

                ctx.update(exclude_sale_line_id=line.id)
                qties = line.product_id._compute_quantities_dict(lot_id=False,owner_id=False,package_id=False)
                qty_enough = qties[line.product_id.id]["virtual_available"] >= (line.product_uom_qty - line.qty_delivered)

                vals = {
                    'qty_enough': qty_enough,
                    "virtual_available": qties[line.product_id.id]["virtual_available"],
                    "qty_available": qties[line.product_id.id]["qty_available"],
                    "incoming_qty": qties[line.product_id.id]["incoming_qty"],
                    "outgoing_qty": qties[line.product_id.id]["outgoing_qty"],
                    #"virtual_stock_conservative": qties[line.product_id.id]["qty_available"] - qties[line.product_id.id]["outgoing_qty"]
                }
                if qties[line.product_id.id]["virtual_available"] == qties[line.product_id.id]["qty_available"]:
                    stock_str = '{}'.format(qties[line.product_id.id]["qty_available"])
                else:
                    stock_str = '{} / {}'.format(qties[line.product_id.id]["virtual_available"], qties[line.product_id.id]["qty_available"])
                vals.update(stock_str = stock_str)
                #print("{}: \n {}".format(line.product_id.display_name, vals))
                line.update(vals)

    qty_enough = fields.Boolean('Qty enough', compute="get_line_qties")

    stock_str = fields.Char('Disponible/Total',
        compute="get_line_qties")
    qty_available = fields.Float(
        "Fisico",
        compute="get_line_qties",
        digits=dp.get_precision("Product Unit of Measure"),
    )
    virtual_stock_conservative = fields.Float(related='product_id.virtual_stock_conservative', string="Disponible")
    virtual_available = fields.Float(
        "Previsto",
        compute="get_line_qties",
        digits=dp.get_precision("Product Unit of Measure"),
    )
    incoming_qty = fields.Float(
        "Entradas",
        compute="get_line_qties",
        digits=dp.get_precision("Product Unit of Measure"),
    )
    outgoing_qty= fields.Float(
        "Salidas",
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
