# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def get_head_order_vals(self, order):
        import ipdb; ipdb.set_trace()
        res = super().get_head_order_vals(order)
        st = self.env['sale.order.type'].\
            search([('telesale', '=', True)], limit=1)
        if st:
            res.update(type_id=st.id)
        return res
