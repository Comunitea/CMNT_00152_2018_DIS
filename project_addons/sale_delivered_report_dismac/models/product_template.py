# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from datetime import datetime, timedelta

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_undelivered_items(self):
        obj_product = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        tree_view = self.env.ref(
            'sale_delivered_report_dismac.view_delivery_report_tree')
        domain = [('product_id', '=', obj_product.id)]
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
