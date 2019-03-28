# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import tools
from odoo import api, fields, models
from lxml import etree


class SaleDelivery(models.Model):
    _name = "sale.delivery.report"
    _description = "Sales Delivery Status"
    _auto = False
    _rec_name = 'date_order'
    _order = 'date_expected asc'

    @api.model
    def fields_view_get(self, view_id=None, view_type='tree', toolbar=False, submenu=False):

        ctx = self._context
        res = super(SaleDelivery, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        print (ctx)
        if view_type == 'form' and ctx.get('product_id', False):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@class='hide_product_id']"):
                print(node)
                node.set('invisible', '0')
            res['arch'] = etree.tostring(doc)
        return res



    @api.multi
    def _get_purchase_order_line(self):
        pol_ids = self.env['purchase.order.line']
        for line in self:
            domain = [('product_id', '=', line.product_id.id), ('qty_to_receive', '!=', 0), ('date_planned', '<=', line.date_expected), ('id', 'not in', pol_ids.ids)]
            pol = self.env['purchase.order.line'].search(domain, order ='date_planned asc', limit=1)
            if pol:
                pol_ids |= pol
                line.purchase_order_line_id = pol.id


    @api.multi
    def _get_qty_to_delivered(self):

        product_id = self.mapped('product_id')
        if not product_id:
            p_id = self._context.get('product_id', False)
            product_id = self.env['product.product'].browse(p_id)
        if len(product_id)!= 1:
            return
        #Compras asociadas pendientes de recibir
        domain = [('product_id', '=', product_id.id), ('qty_to_receive', '!=', 0)]
        pol = self.env['purchase.order.line'].search(domain, order ='date_planned asc')

        qty_available = product_id.qty_available
        qty_reserved = 0.00

        for line in self.filtered(lambda x: x.product_id == product_id).sorted(key='date_expected', reverse=False):
            pol_line_ids = pol.filtered(lambda x: x.date_planned < line.date_expected)

            line.qty_to_receive = sum(x.qty_to_receive for x in pol_line_ids)
            if pol_line_ids:
                pol -= pol_line_ids
                line.purchase_order_line_id = pol_line_ids[0].id
                line.date_planned = pol_line_ids[0].date_planned
                line.purchase_order_ids = [(6, 0, pol_line_ids.mapped('order_id').ids)]
            line.qty_to_delivered = line.sml_ordered_qty - line.qty_delivered - line.sml_qty_canceled
            line.qty_available_to_delivered = qty_available + sum(x.qty_to_receive for x in pol_line_ids)
            line.qty_reserved += line.qty_to_delivered
            qty_reserved  += line.qty_to_delivered
            qty_available -= line.qty_to_delivered

            line.sendable = line.qty_available_to_delivered >= line.qty_to_delivered

    product_id = fields.Many2one('product.product', readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True)
    sale_order_id = fields.Many2one('sale.order', readonly=True)
    sale_order_line_id = fields.Many2one('sale.order.line', readonly=True)
    stock_move_id = fields.Many2one('stock.move', readonly=True)
    date_order = fields.Datetime(related='sale_order_id.date_order', readonly=True)
    date_expected = fields.Datetime(related='stock_move_id.date_expected', readonly=True)
    state = fields.Selection(related='sale_order_id.state', readonly=True)
    actual_status = fields.Selection(selection=[('in_progress', 'En proceso'), ('sent', 'Enviado'), ('cancel', 'Cancelado')], readonly=True)
    sml_ordered_qty = fields.Float('Qty Ordered', readonly=True)  
    qty_delivered = fields.Float(related='sale_order_line_id.qty_delivered', readonly=True)
    sml_qty_canceled = fields.Float('Qty Canceled', readonly=True)
    qty_available = fields.Float(related='product_id.qty_available', readonly=True)
    purchase_order_line_id = fields.Many2one(compute="_get_qty_to_delivered")
    qty_to_receive = fields.Float(compute="_get_qty_to_delivered")
    date_planned = fields.Datetime(compute="_get_qty_to_delivered")
    purchase_order_ids = fields.Many2many('purchase.order', compute="_get_qty_to_delivered")
    qty_reserved = fields.Float(compute="_get_qty_to_delivered")
    qty_to_delivered = fields.Float(compute="_get_qty_to_delivered")
    qty_available_to_delivered = fields.Float(compute="_get_qty_to_delivered")
    sendable = fields.Float(compute="_get_qty_to_delivered")

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.id as sale_order_line_id,
                    l.product_id as product_id,
                    l.order_id as sale_order_id,
                    sm.id as stock_move_id,
                    partner.id as partner_id,
                    (select SUM(sm.ordered_qty) from stock_move sm where sm.sale_line_id = l.id) as sml_ordered_qty,
                    l.qty_delivered as qty_delivered,
                    (select SUM(sm.ordered_qty) from stock_move sm where sm.sale_line_id = l.id and sm.state = 'cancel') as sml_qty_canceled,
                    case
                        when ((select SUM(sm.ordered_qty) from stock_move sm where sm.sale_line_id = l.id) =
                         (select SUM(sm.ordered_qty) from stock_move sm where sm.sale_line_id = l.id and sm.state = 'cancel')) then 'cancel'
                        when ((select SUM(sm.ordered_qty) from stock_move sm where sm.sale_line_id = l.id) = qty_delivered) then 'sent'
                        else 'in_progress'
                    end as actual_status  
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _from(self):
        from_str = """
                sale_order_line l
                      join sale_order s on (l.order_id=s.id)
                      join stock_move sm on (l.id = sm.sale_line_id)
                      join res_partner partner on s.partner_id = partner.id
                      left join stock_move_line sml on (sm.id = sml.move_id)     
        """
        return from_str

    def _group_by(self):
        group_by_str = """

            GROUP BY l.product_id,
                    l.qty_delivered,
                    sm.state,
                    l.id,
                    sm.id,
                    partner.id
        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            ) order by date_expected""" % (self._table, self._select(), self._from(), self._group_by()))
    
    
    @api.multi
    def _update_status(self):
        for var in self:
            if var.actual_status == 'in_progress':
                restante = var.sml_ordered_qty - var.qty_delivered - var.sml_qty_canceled
                if var.qty_available < restante:
                    var.sendable = 0
                else:
                    var.sendable = 1
            else:
                var.sendable = 2

        