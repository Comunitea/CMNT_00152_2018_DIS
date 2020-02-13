# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    delivered_qty = fields.Float("Cantidad entregada hasta 31/01")
    #remain_qty = fields.Float("Pending quantity on Date")
    subtotal_delivered_date = fields.Float(
        string='Valor entregado hasta 31/01',
    )
    delivery_until = fields.Date(
        store=False, search=lambda operator, operand, vals: []
    )
    type_id = fields.Many2one('sale.order.type', 'Tipo', readonly=True)
    
    

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        if fields is None:
            fields = {}
        select_str = """ ,
            sum((l.price_subtotal /
                 coalesce(nullif(l.product_uom_qty, 0), 1)
                ) * d.delivered_qty)
            as subtotal_delivered_date
        """
        fields.update({
            'subtotal_delivered_date': select_str,
            'delivered_qty': " ,d.delivered_qty as delivered_qty",
            'type_id': ", s.type_id as type_id",

            #'remain_qty': " , l.product_uom_qty - d.delivered_qty as remain_qty",
        })
        from_clause += " left join (SELECT sum(quantity) as delivered_qty, min(line_id) as line_id FROM sale_order_line_delivery " \
                       " GROUP BY line_id) d on (d.line_id = l.id)"
        groupby += ", d.delivered_qty, s.type_id"
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
1