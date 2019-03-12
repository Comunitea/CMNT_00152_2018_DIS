# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import tools
from odoo import api, fields, models

class SaleDelivery(models.Model):
    _name = "sale.delivery.report"
    _description = "Sales Delivery Status"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    name = fields.Char('Order Reference', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    date = fields.Datetime('Date Order', readonly=True)
    date_expected = fields.Datetime('Expected Date', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)
    actual_status = fields.Selection(selection=[('in_progress', 'En proceso'), ('sent', 'Enviado'), ('cancel', 'Cancelado')], readonly=True)
    partner_name = fields.Char('Partner Name', readonly=True)
    sml_ordered_qty = fields.Float('Qty Ordered', readonly=True)  
    qty_delivered = fields.Float('Qty Delivered', readonly=True)
    sml_qty_canceled = fields.Float('Qty Canceled', readonly=True)
    qty_available = fields.Float(related='product_id.qty_available', readonly=True)
    sendable = fields.Float(compute="_update_status", readonly=True)
      
    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT min(l.id) as id,
                    l.name as product_name,
                    l.product_id as product_id,
                    s.name as name,
                    s.date_order as date,
                    sm.date_expected as date_expected,
                    s.state as state,
                    partner.name as partner_name,
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

            GROUP BY l.name,
                     l.product_id,
                    s.name,
                    s.date_order,
                    sm.date_expected,
                    s.state,
                    partner.name,
                    s.user_id,
                    l.product_uom_qty,
                    l.qty_delivered,
                    sm.state,
                    l.id,
                    sm.id
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

        