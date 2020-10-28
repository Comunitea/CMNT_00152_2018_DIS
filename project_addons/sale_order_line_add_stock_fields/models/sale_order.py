# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    def get_line_qties(self):

        # print ("\n--------------------------\n##ENTRO EN EN GET_LINE_QTIES\n--------------------------")
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
        # import pdb; pdb.set_trace()
        # so_ids = self.with_prefetch().mapped('order_id')
        # move_domain = [('sale_line_id', 'in', so_ids.mapped('order_line').ids), ('state', 'not in', ('draft', 'cancel', 'done')), ('location_dest_id.usage', '=', 'customer')]
        # need_qty = self.env['stock.move'].read_group(move_domain, ['sale_line_id'], ['product_uom_qty'])
        # print (need_qty)
        for line in self.filtered('product_id'):
            ctx.update(location=line.order_id.warehouse_id.lot_stock_id.id, exclude_sale_line_id=line.id)
            product_id = line.product_id.with_context(ctx)
            move_domain = [('sale_line_id', '=', line.id), ('state', 'not in', ('draft', 'cancel', 'done')), ('location_dest_id.usage', '=', 'customer')]
            need_qty = self.env['stock.move'].read_group(move_domain, ['sale_line_id'], ['product_uom_qty'])
            qties = product_id._compute_quantities_dict(lot_id=False,owner_id=False,package_id=False)
            print (qties)
            if need_qty:
                qty_enough = qties[product_id.id]["virtual_available"] >= need_qty[0]['product_uom_qty']
            else:
                qty_enough = True
            #
            # vals = {
            #     'qty_enough': qty_enough,
            #     "virtual_available": qties[product_id.id]["virtual_available"],
            #     "line_qty_available": qties[product_id.id]["qty_available"],
            #     "incoming_qty": qties[product_id.id]["incoming_qty"],
            #     "outgoing_qty": qties[product_id.id]["outgoing_qty"],
            #     #"virtual_stock_conservative": qties[line.product_id.id]["qty_available"] - qties[line.product_id.id]["outgoing_qty"]
            # }
            # if qties[line.product_id.id]["virtual_available"] == qties[line.product_id.id]["qty_available"]:
            #     stock_str = '{}'.format(qties[line.product_id.id]["qty_available"])
            # else:
            #     stock_str = '{} / {}'.format(qties[line.product_id.id]["virtual_available"], qties[line.product_id.id]["qty_available"])
            # vals.update(stock_str = stock_str)
            # line.write(vals)
            #print("{}: \n {}".format(line.product_id.display_name, vals))
            line.qty_enough = qty_enough
            line.line_qty_available = qties[product_id.id]["qty_available"]
            line.incoming_qty = qties[product_id.id]["incoming_qty"]
            line.outgoing_qty = qties[product_id.id]["outgoing_qty"]
            line.virtual_available = qties[product_id.id]["virtual_available"]

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

    @api.multi
    def compute_line_virtual_stock_conservative(self):
        for line in self:
            line.virtual_stock_conservative = line.product_id.virtual_stock_conservative


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
