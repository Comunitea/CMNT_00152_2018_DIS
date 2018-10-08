# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartner(models.Model):

    _inherit = 'res.partner'

    avoid_locks = fields.Boolean('Avoid locks')
    lock_orders = fields.Boolean('Lock Orders', compute='_compute_locks')
    min_no_shipping = fields.Float('Min No Shipping Cost')

    @api.multi
    def _compute_locks(self):
        for partner in self.filtered('customer'):
            if not partner.avoid_locks:
                partner.lock_orders = partner.risk_exception

    @api.multi
    def recompute_sale_order_locks(self):
        """
        Get orders to recompute the lock checkboxes
        """
        for partner in self:
            domain = [
                ('partner_id', 'child_of',
                 partner.commercial_partner_id.id),
                ('state', 'not in', ['done, cancel'])
            ]
            sale_objs = self.env['sale.order'].search(domain)
            sale_objs.check_locks()

    @api.multi
    def write(self, vals):
        """
        When update the avoid_lock check we must recompute the
        related_sale_orders
        """
        res = super(ResPartner, self).write(vals)
        if 'avoid_locks' in vals or 'min_no_shipping' in vals:
            self.recompute_sale_order_locks()
        return res
