# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_view_line_history(self):
        tree_view = self.env.ref(
            'sale_line_history.sale_order_line_history_view_tree')
        domain = [
            ('state', 'in', ['sale', 'done']),
            ('order_partner_id', 'child_of',
             self.commercial_partner_id.id),
            ('display_type', '=', False)]
        return {
            'name': 'Sales history',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'sale.order.line',
            'views': [(tree_view.id, 'tree')],
            'domain': domain
        }
