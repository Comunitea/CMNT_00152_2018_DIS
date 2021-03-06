# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from dateutil import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    estimated_delivery_date = fields.Date("Entrega estimada", compute='get_line_estimated_delivery_date')
    purchase_order_needed = fields.Many2one('purchase.order', string="Compra para entrega", compute = 'get_line_estimated_delivery_date', help="Compra que traerá la mercancía necesaria para la entrega")
    move_needed = fields.Many2one('stock.move', string="Moviento para entrega", compute = 'get_line_estimated_delivery_date')
    partner_id = fields.Many2one(related='order_id.partner_id', string="Empresa", store=True)
    moves_state = fields.Selection([('none', 'Sin movimientos'), ('pending', 'Pendientes'), ('done', 'Finalizado')], string='Estado almacén', compute="get_warehouse_state", store=True)
    expected_date = fields.Datetime(related="order_id.expected_date", string="Entrega en pedido")
    outgoing_pending = fields.Boolean('Entregas pendientes', compute = 'get_line_estimated_delivery_date')

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        # TDE FIXME: strange

        if self._context.get('buy_pending', False) and limit:
            new_limit = limit
            purchases = self.env['sale.order.line']
            res = []
            new_off = offset
            while len(purchases) < new_limit  or not res:
                res = super(SaleOrderLine, self)._search(args, offset=new_off, limit=new_limit, order=order, count=count,
                                                   access_rights_uid=access_rights_uid)
                limit += len(res)
                if not res:
                    break
                purchases += self.browse(res).filtered(lambda x: x.purchase_order_needed)
                new_off += len(res)
            args += [('id', 'in', purchases.ids)]

        return super()._search(args=args, offset=offset, limit=limit, order=order, count=count,
                                                   access_rights_uid=access_rights_uid)


    @api.depends('move_ids.state')
    @api.multi
    def get_warehouse_state(self):
        for line in self:
            if not line.move_ids:
                state = 'none'
            else:
                if all(move.state in ('done', 'cancel', 'draft') for move in line.move_ids):
                    state = 'done'
                else:
                    state = 'pending'
            line.moves_state = state

    def get_loc_domain(self, estimated_date):

        wh_id = self.order_id.warehouse_id
        parent_path = wh_id.view_location_id.parent_path

        domain_out = expression.AND([[('date_expected', '<=', estimated_date)], [('location_id.parent_path', 'ilike', parent_path +'%')],['!', ('location_dest_id.parent_path', 'ilike', parent_path +'%')]])
        domain_in = expression.AND([[('location_dest_id.parent_path', 'ilike', parent_path + '%')], ['!', ('location_id.parent_path', 'ilike', parent_path +'%')]])
        return wh_id, expression.OR([domain_in, domain_out])

    def get_pending_moves_for_lines(self, usage='customer'):
        if len(self) == 1:
            where = "sm.sale_line_id = {} ".format(self.id)
        else:
            where = "sm.sale_line_id in {} ".format(tuple(self.ids))
        sql = "select sale_line_id, count(sm.id) as n_moves, sum(sm.product_uom_qty) as product_uom_qty, so.id " \
              "from stock_move sm " \
              "join sale_order_line sol on sol.id = sm.sale_line_id " \
              "join sale_order so on so.id = sol.order_id " \
              "join stock_location sl on sl.id = sm.location_dest_id " \
              "where sl.usage = '{}' and sm.state not in ('draft', 'done', 'cancel') and {}" \
              "group by sale_line_id, so.id".format(usage, where)
        self._cr.execute(sql)
        moves = self._cr.fetchall()
        res = {}
        for m in moves:
            res[m[0]] = {'num': m[1], 'product_uom_qty': m[2], 'sale_id': m[3]}
        return res



    @api.multi
    def get_line_estimated_delivery_date(self):
        today = fields.Datetime.today()
        ctx = self._context.copy()
        wh_id = False
        loc_domain = []
        sm = self.env['stock.move']
        ctx = self._context.copy()
        moves_pending = self.get_pending_moves_for_lines()

        for line in self:
            if not line.id in moves_pending.keys():
                line.outgoing_pending = False
                # print ('La línea {} not tienen nada pendiente'.format(line.id))
                continue
            line.outgoing_pending = True
            ctx.update(location=line.order_id.warehouse_id.lot_stock_id.id)
            #
            # domain = [('sale_line_id', '=', line.id), ('state', 'in', ('assigned', 'partially_available', 'confirmed'))]
            # line_moves = sm.search(domain).filtered(lambda x: not x.move_orig_ids)
            # if all(x.state == 'assigned' for x in line_moves.filtered(lambda x: x.location_dest_id.usage == 'customers')):
            #
            #
            # outgoing_qty = sum(x.poduct_uom_qty for x in line_moves.filtered(lambda x: x.location_id.usage == 'internal' and x.location_dest_id.usage == 'customers'))
            # incoming_qty = sum(x.poduct_uom_qty for x in line_moves.filtered(lambda x: x.location_id.usage == 'customers' and x.location_dest_id.usage == 'internal'))
            # line_qty_pending = outgoing_qty - incoming_qty
            #

            line_moves = line.move_ids.filtered(lambda x: not x.move_orig_ids)
            if line_moves:
                estimated_date = line_moves[0].date_expected
            else:
                estimated_date = line.order_id.expected_date or line.order_id.confirmation_date or line.order_id.date_order
            ##SI TODOS LOS MOVIMEINTOS DE LA LINEA ESTÁN ASIGNADOS

            if line_moves and all(x.state=='assigned' for x in line_moves):
                date_expected = max(today, max(x.date_expected for x in line_moves))
                line.estimated_delivery_date = (date_expected + relativedelta.relativedelta(days=1 or 0)).strftime(DEFAULT_SERVER_DATE_FORMAT)
                continue

            need_qty = line.product_uom_qty

            #location = line.order_id.warehouse_id.lot_stock_id
            #parent_path = '{}/'.format(location.id)
            #ctx.update(location=location.id)
            product_id = line.product_id.with_context(ctx)
            available_qty = product_id.qty_available
            ##NO ESTÁ CONFIRMADO EL PEDIDO O LA LINEA PERO HAY CANTIDAD DISPONIBLE
            if not line.move_ids and available_qty > need_qty:
                estimated_date = max(today, estimated_date)
                line.estimated_delivery_date = (estimated_date + relativedelta.relativedelta(days=1 or 0)).strftime(DEFAULT_SERVER_DATE_FORMAT)
                continue
            ##BAJO PEDIDO
            if line.move_ids and line.move_ids.mapped("created_purchase_line_id"):
                # print("--- TIene una compra asociada {}".format(
                #     line.move_ids.mapped("created_purchase_line_id").mapped('order_id').mapped('name')))
                purchase_line = line.move_ids.mapped("created_purchase_line_id")
                ## si ya tiene movimientos
                if purchase_line.mapped('move_ids'):
                    # cojo el ultimo movimiento ordenado por fecha de llegada
                    last_move = purchase_line.mapped('move_ids').sorted('date_expected', reverse=True)[0]
                    line.purchase_order_needed = purchase_line.order_id

                    estimated_date = max(last_move.date_expected, estimated_date)
                    line.estimated_delivery_date = (estimated_date +
                                                    relativedelta.relativedelta(days=1 or 0)).strftime(
                        DEFAULT_SERVER_DATE_FORMAT)
                else:
                    line.purchase_order_needed = purchase_line.order_id
                    line.estimated_delivery_date = False
                continue

            if not wh_id or wh_id != line.order_id.warehouse_id:
                wh_id, loc_domain = line.get_loc_domain(estimated_date.strftime(DEFAULT_SERVER_DATE_FORMAT))

            moves_domain = [('state', '=', 'assigned'), ('created_purchase_line_id', '=', False),
                            ('product_id', '=', product_id.id),
                            ('location_id.usage', '=', 'supplier'), ('location_dest_id.usage', '=', 'internal')]
            move = self.env['stock.move'].search(moves_domain, order='date_expected asc', limit = 1)
            po = self.env['purchase.order']
            line.estimated_delivery_date = False
            if move:
                line.purchase_order_needed = move.purchase_line_id and move.purchase_line_id.order_id or False
                #estimated_date = max(today, move.date_expected)
                if move.date_expected:
                    #estimated_date = max(today, move.date_expected)
                    estimated_date = move.date_expected
                    line.estimated_delivery_date = (estimated_date + relativedelta.relativedelta(days=1 or 0)).strftime(
                        DEFAULT_SERVER_DATE_FORMAT)
                    line.move_needed = move
            continue
            # for move in moves:
            #     ##
            #     if move.created_purchase_line_id:
            #         ##bajo pedido
            #         #print("---Bajo pedido. No afecta al stock")
            #         if move.sale_line_id == line:
            #             move_orig_ids = move.move_orig_ids.filtered(lambda x: x.state not in ('draft', 'cancel'))
            #             if move_orig_ids:
            #                 ##bajo pedido de la línea de venta
            #                 #print("Movimeinto bajo pedido {} para el pedido {} CON movimeintos de destino enel albaran {}".format(move.created_purchase_line_id.order_id.name, line.order_id.name, move.picking_id.name))
            #                 purchase_moves_id = move_orig_ids[0]
            #                 line.purchase_order_needed = purchase_moves_id.purchase_line_id.order_id
            #                 estimated_date = max(today, purchase_moves_id.date_expected )
            #                 line.estimated_delivery_date = (estimated_date + relativedelta.relativedelta(days=1 or 0)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            #                 ## linea de venta completa, voy a la siguiente linea
            #                 break
            #             else:
            #                 print("ERROR:---------------\nMovimeinto bajo pedido {} para el pedido {} sin movimeintos de destino enel albaran {}".format(move.created_purchase_line_id.order_id.name, line.order_id.name, move.picking_id.name))
            #         #bajo pedido solo afecta a la propia linea de venta
            #         continue
            #
            #     if move.purchase_line_id and move.move_dest_ids and move.move_dest_ids[0].created_purchase_line_id == move.purchase_line_id:
            #         ## es un pedido de compra bajo pedido. Ignoro el movimeinto y voy al siguiente movimiento
            #         #print("---Entrada de una compra bajo pedido {}. No afecta al stock".format(move.purchase_line_id.order_id.name))
            #         continue
            #
            #     if move.sale_line_id == line:
            #         ## movimeinto de la línea: Tengo stock sufcicente para servirlo. VOy a la siguiente linea
            #         if available_qty > need_qty:
            #             estimated_date = max(today, move.date_expected )
            #             line.estimated_delivery_date = (estimated_date + relativedelta.relativedelta(days=1 or 0)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            #             break
            #
            #     if not move.sale_line_id and  move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal' and move.date_expected <= estimated_date:
            #         ##Movieminto de salida de stock
            #         ## Si es posterior a la fecha del movimeinto de la línea, estonces lo ignoro ya que no afecta
            #         #print ('El movimineto {}-{} es un envío a clientes: {}'.format(move.id, move.name, move.picking_id.name))
            #         # if move.date_expected > estimated_date:
            #         #     continue
            #         outgoing = True
            #         # Desuenta stock disponible
            #         available_qty = available_qty - move.product_uom_qty
            #
            #     elif move.location_dest_id.usage == 'internal' and move.location_id.usage != 'internal':
            #         #print('El movimineto {}-{} es una entrada a stcok: {}'.format(move.id, move.name,move.picking_id.name))
            #         ## Es una entrada en stock
            #         if available_qty < need_qty and available_qty + move.product_uom_qty >= need_qty:
            #
            #             line.purchase_order_needed = move.purchase_line_id and move.purchase_line_id.order_id or False
            #             estimated_date = max(today, move.date_expected )
            #             line.estimated_delivery_date = (estimated_date + relativedelta.relativedelta(days=1 or 0)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            #             line.move_needed = move
            #             break
            #         outgoing = False
            #         available_qty = available_qty + move.product_uom_qty















