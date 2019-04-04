# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from datetime import datetime, timedelta

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_unreceived_sale_lines(self):
        tree_view = self.env.ref(
            'sale_delivered_report_dismac.view_delivery_report_tree')
        domain = [('product_id', '=', self.product_id.id)]
        return {
            'name': 'Sales delivery report',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.delivery.report',
            'views': [(tree_view.id, 'tree')],
            'domain': domain,
            'context': {'search_default_not_delivered': 1}
        }

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super().product_uom_change()
        #self._get_date_planned()
        return res

    def _get_qty_canceled(self):
        sql_sum = "select SUM(ordered_qty) from stock_move where state = 'cancel' and sale_line_id = {}"
        for line in self:
            if line.product_id:
                sql = sql_sum.format(line.id)
                self._cr.execute(sql)
                res = self._cr.fetchall()
                if res:
                    line.qty_canceled = res[0][0]
                else:
                    line.qty_canceled = 0.0

    def _get_date_planned(self):
        ctx = self._context.copy()
        for line in self:
            if line.product_id:
                if line.product_uom_qty > (line.qty_canceled + line.qty_delivered):
                    ctx.update(product_id=line.product_id.id)
                    domain = [('product_id', '=', line.product_id.id), ('actual_status', 'in', ['in_progress', 'cancel'])]
                    sl_report = self.with_context(ctx).env['sale.delivery.report'].search(domain)
                    if sl_report:
                        sl_line = sl_report.filtered(lambda x: x.date_order <= line.order_id.date_order).sorted(key=lambda x: x.date_order, reverse=True)
                        line.planned_delivery_date = sl_line[0] and (sl_line[0].date_planned or sl_line[0].date_expected)



    planned_delivery_date= fields.Date("Estimated delivery date", compute="_get_date_planned")
    qty_canceled = fields.Float('Qty Canceled', compute="_get_qty_canceled")
