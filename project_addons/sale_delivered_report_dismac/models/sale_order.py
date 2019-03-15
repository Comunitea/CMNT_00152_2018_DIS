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