# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from datetime import datetime, timedelta


class ResPartner(models.Model):
    _inherit = "res.partner"

    def get_undelivered_items(self):


        action = self.env.ref('sale_delivered_report_dismac.action_delivery_report_all').read()[0]
        action['views'] = [
            (self.env.ref('sale_delivered_report_dismac.view_delivery_order_line_tree').id, 'tree'),
        ]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = self._context
        return action



        tree_view = self.env.ref(
            "sale_delivered_report_dismac.view_delivery_report_tree"
        )
        domain = [("partner_id", "=", self.id)]
        return {
            "name": "Sales delivery report",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "sale.delivery.report",
            "views": [(tree_view.id, "tree")],
            "domain": domain,
            "context": {"search_default_not_delivered": 1},
        }
