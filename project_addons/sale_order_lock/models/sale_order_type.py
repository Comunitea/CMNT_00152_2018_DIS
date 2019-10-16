# Copyright 2015-2017 Eficent
# - Jordi Ballester Alomar
# Copyright 2015-2017 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models, api


class SaleOrderType(models.Model):

    _inherit = "sale.order.type"

    min_margin = fields.Float(
        "Min Margin",
        help="If Margin of sale order \
        is below the min_margin the order will be locked",
    )

    @api.multi
    def recompute_sale_order_locks(self):
        """
        Get orders to recompute the lock checkboxes
        """
        for sale_type in self:
            domain = [
                ("type_id", "=", sale_type.id),
                ("state", "not in", ["done, cancel"]),
            ]
            sale_objs = self.env["sale.order"].search(domain)
            sale_objs.check_locks()

    @api.multi
    def write(self, vals):
        """
        When update the avoid_lock check we must recompute the
        related_sale_orders
        """
        res = super().write(vals)
        if "min_margin" in vals:
            self.recompute_sale_order_locks()
        return res
