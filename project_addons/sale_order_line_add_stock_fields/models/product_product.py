# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ProductProduct(models.Model):

    _inherit = "product.product"

    def _get_domain_locations_new(self, location_ids, company_id=False, compute_child=True):
        d_quant, d_in, d_out = super()._get_domain_locations_new(location_ids=location_ids, company_id=company_id, compute_child=compute_child)

        if self._context.get('exclude_sale_line_id', False):
            sol_ids = self._context['exclude_sale_line_id']
            d_out = [('sale_line_id', 'not in', sol_ids)] + d_out
        return d_quant, d_in, d_out
