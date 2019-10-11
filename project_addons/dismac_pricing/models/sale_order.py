# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models
from datetime import date


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    def create_customer_prices(self):
        for line in self.order_line:
            custom_price = self.env['customer.price'].get_customer_price_rec(
                self.partner_id, line.product_id, line.product_uom_qty)
            if custom_price:
                custom_price.date_end = date.today()
            self.env['customer.price'].create({
                'product_id': line.product_id.id,
                'partner_id': self.partner_id.id,
                'price': line.price_unit
            })
