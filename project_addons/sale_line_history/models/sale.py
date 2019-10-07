# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_view_line_history(self):
        tree_view = self.env.ref(
            'sale_line_history.sale_order_line_history_view_tree')
        context = {'order_id': self.id}
        domain = [
            ('state', 'in', ['sale', 'done']),
            ('order_partner_id', 'child_of',
             self.partner_id.commercial_partner_id.id),
            ('display_type', '=', False)]
        return {
            'name': 'Sales history',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'sale.order.line',
            'views': [(tree_view.id, 'tree')],
            'context': context,
            'domain': domain
        }


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    date_order = fields.Datetime(related='order_id.date_order', readonly=True)
