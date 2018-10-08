# Copyright 2015-2017 Eficent
# - Jordi Ballester Alomar
# Copyright 2015-2017 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models, api


class OperatingUnit(models.Model):

    _inherit = 'operating.unit'
    _description = 'Operating Unit'

    min_margin = fields.Float('Min Margin', help="If Margin of sale order \
        is below the min_margin the order will be locked")

    @api.multi
    def recompute_sale_order_locks(self):
        """
        Get orders to recompute the lock checkboxes
        """
        for op in self:
            domain = [
                ('team_id.operating_unit_id', '=', op.id),
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
        res = super(OperatingUnit, self).write(vals)
        if 'min_margin' in vals:
            self.recompute_sale_order_locks()
        return res
