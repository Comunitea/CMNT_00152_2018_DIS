# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_unreceived_items(self):
        obj_product = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        model_data = self.env['ir.model.data']

        tree_view = model_data.get_object_reference(
            'purchase_custom_dismac', 'purchase_custom_tree')
        search_view = model_data.get_object_reference(
            'purchase_custom_dismac', 'purchase_custom_search')
        domain = [('product_id', '=', obj_product.id)]
        value = {}
        for call in self:
            value = {
                'name': _('Purchase order lines'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'purchase.order.line',
                'views': [
                    (tree_view and tree_view[1] or False, 'tree')],
                'type': 'ir.actions.act_window',
                'domain': domain,
                'search_view_id': search_view and search_view[1] or False,
                'context': {'search_default_not_delivered': 1}
            }
        return value