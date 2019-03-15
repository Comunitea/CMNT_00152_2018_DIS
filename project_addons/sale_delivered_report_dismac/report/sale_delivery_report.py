# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import tools
from odoo import api, fields, models

class SaleDelivery(models.Model):
    _name = "sale.delivery.report"
    _description = "Sales Delivery Status"
    _auto = False
    _rec_name = 'date_order'
    _order = 'date_order desc'

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
    sendable = fields.Float(compute="_update_status", readonly=True)
      
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
            )""" % (self._table, self._select(), self._from(), self._group_by()))
    
    
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

        