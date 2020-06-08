# © 2014 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.tools.profiler import profile


class SaleOrder(models.Model):
    _inherit = "sale.order"

    margin_perc = fields.Float(compute="_product_margin",
                               string='Margin %',
                               help="It gives profitability by calculating "
                                    "percentage.", store=True)
    margin = fields.Monetary(compute='_product_margin',
                             help="It gives profitability by calculating\
                                  the difference between the Unit Price \
                                      and the cost.",
                             currency_field='currency_id',
                             digits=dp.get_precision('Product Price'),
                             store=True)

    #@profile
    @api.depends('order_line.margin')
    @api.multi
    def _product_margin(self):
        for order in self:
            margin = sum(order.order_line.filtered(
                lambda r: r.state != 'cancel').mapped('margin'))
            if order.amount_untaxed:
                margin_perc = round((margin * 100) /
                                         order.amount_untaxed, 2)
            else:
                margin_perc = 0
           
            order.update({
                'margin_perc': margin_perc,
                'margin': margin,
            })



class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    margin = fields.Float(compute='_product_margin',
                          digits=dp.get_precision('Product Price'),
                          store=True)
    purchase_price = fields.Float(compute='_product_margin',
                                  string="Cost",
                                  digits=dp.get_precision("Product Price"))

    #@profile
    def _compute_cost_price(self):
        frm_cur = self.env.user.company_id.currency_id
        to_cur = self.order_id.pricelist_id.currency_id
        purchase_price = self.product_id.reference_cost or \
                         self.product_id.standard_price
        if self.product_uom != self.product_id.uom_id:
            purchase_price = self.product_id.uom_id._compute_price(
                purchase_price, self.product_uom)
        price = frm_cur._convert(
            purchase_price, to_cur,
            self.order_id.company_id or self.env.user.company_id,
            self.order_id.date_order or fields.Date.today(), round=False)
        return price

    #@profile
    @api.depends('product_id', 'product_uom_qty',
                 'price_unit', 'price_subtotal')
    def _product_margin(self):
        for line in self:
            if line.product_id.type != 'product':
                line.margin = 0
            else:
                # currency = line.order_id.pricelist_id.currency_id
                price = line._compute_cost_price()
                line.purchase_price = price
                line.margin = line.price_subtotal - \
                              (price * line.product_uom_qty)
