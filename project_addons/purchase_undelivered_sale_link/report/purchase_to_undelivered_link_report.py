# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import tools
from odoo import api, fields, models
from lxml import etree
from odoo.addons import decimal_precision as dp

class PurchaseUndeliveredLinkReport(models.Model):
    _name = "purchase.undelivered.link.report"
    _description = "Purchase to undelivered link report"
    _auto = False
    _rec_name = 'sale_order_id'
    _order = 'date_order asc'

    product_id = fields.Many2one('product.product', readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True)

    sale_order_id = fields.Many2one('sale.order', readonly=True)
    sale_line_id = fields.Many2one('sale.order.line', readonly=True)

    so_state = fields.Char("Order state", readonly=True)
    sm_state = fields.Char("Move state", readonly=True)
    date_order = fields.Datetime("Order date", readonly=True)
    product_uom_qty = fields.Float('Qty Ordered', readonly=True, digits=dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one('product.uom', string='Product Unit of Measure', required=True)
    qty_delivered = fields.Float('Qty delivered', readonly=True)
    qty_to_delivered = fields.Float('Qty to delivered', readonly=True)
    qty_cancelled = fields.Float('Qty Canceled', readonly=True, digits=dp.get_precision('Product Unit of Measure'))
    picking_id = fields.Many2one('stock.picking', readonly=True)
    company_id = fields.Many2one('res.company', readonly=1)

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             select
             min(sol.id) as id,
             so.id as sale_order_id,
             so.partner_id as partner_id,
             so.date_order as date_order,
             sol.product_id as product_id,
             sol.product_uom_qty,
             sol.product_uom,
             sol.qty_delivered,
             sol.qty_cancelled,
             sol.product_uom_qty - sol.qty_delivered- sol.qty_cancelled as qty_to_delivered,
             sm.picking_id as picking_id,
             sm.sale_line_id as sale_line_id,
             so.company_id as company_id,
             sm.state as sm_state,
             so.state as so_state

        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _from(self):
        from_str = """
                stock_move sm
                join stock_location sl on sl.id = sm.location_id
                join sale_order_line sol on sol.id = sm.sale_line_id
                join sale_order so on so.id = sol.order_id
                """
        return from_str

    def _where(self):
        where = """
                sm.state in ('partially_available','confirmed')
                """
        return where

    def _group_by(self):
        group_by_str = """

            group by
                so.id,
                sol.id,
                so.partner_id,
                so.date_order,
                sol.product_id,
                sol.product_uom_qty,
                sol.qty_delivered,
                sol.qty_cancelled,
                sm.picking_id,
                sm.sale_line_id,
                so.company_id,
                sm.state,
                so.state, sol.product_uom

        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            WHERE ( %s )
            %s
            order by so.date_order)
            """ % (self._table, self._select(), self._from(), self._where(), self._group_by())
        self.env.cr.execute(sql)
