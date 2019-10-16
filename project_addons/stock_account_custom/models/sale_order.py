# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    margin = fields.Float(
        compute="_product_margin",
        digits=dp.get_precision("Product Price"),
        store=True,
    )
    purchase_price = fields.Float(
        string="Cost", digits=dp.get_precision("Product Price")
    )

    def _compute_margin(self, order_id, product_id, product_uom_id):
        frm_cur = self.env.user.company_id.currency_id
        to_cur = order_id.pricelist_id.currency_id
        purchase_price = product_id.reference_cost
        if product_uom_id != product_id.uom_id:
            purchase_price = product_id.uom_id._compute_price(
                purchase_price, product_uom_id
            )
        price = frm_cur._convert(
            purchase_price,
            to_cur,
            order_id.company_id or self.env.user.company_id,
            order_id.date_order or fields.Date.today(),
            round=False,
        )
        return price
