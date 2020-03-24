# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.onchange('product_id')
    def product_id_change(self):
        res = super().product_id_change()
        date = self.order_id.date_order or fields.Date.context_today(self)
        price_and_discount = self.product_id._get_price_and_discount (self.product_uom_qty, self.partner_id, date)
        self.price_unit = price_and_discount['price']
        if not self.discount:   
            self.discount = price_and_discount['discount']
        return res