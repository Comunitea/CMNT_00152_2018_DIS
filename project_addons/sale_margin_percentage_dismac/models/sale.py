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
    order_coef = fields.Float(compute="_product_coef",
                               string='Coeficiente',
                               help="Coefciente de venta", store=True)
    order_ref_coef = fields.Float(compute="_product_coef",
                               string='Coeficiente ref.',
                               help="Coefciente de venta (ref)", store=True)
    order_cost = fields.Float(compute="_product_coef",
                               string='Coste de venta',
                               help="Coste de venta", store=True)
    
    order_ref_cost = fields.Float(compute="_product_coef",
                               string='Coste de venta (ref)',
                               help="Coste de venta (ref)", store=True)

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

    @api.depends('order_line.line_ref_cost', 'order_line.line_cost',
                'order_line.price_subtotal')
    @api.multi
    def _product_coef(self):
        for order in self:
            order_cost = sum(order.order_line.filtered(
                lambda r: r.state != 'cancel').mapped('line_cost'))
            order_ref_cost = sum(order.order_line.filtered(
                lambda r: r.state != 'cancel').mapped('line_ref_cost'))
            if order_cost:
                order_coef = round(order.amount_untaxed / order_cost, 2)
            else:
                order_coef = 1
            if order_ref_cost:
                order_ref_coef = round(order.amount_untaxed / order_ref_cost, 2)
            else:
                order_ref_coef = 1
           
            order.update({
                'order_coef': order_coef,
                'order_ref_coef': order_ref_coef,
                'order_cost': order_cost,
                'order_ref_cost': order_ref_cost
            })


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    margin = fields.Float(compute='_product_margin',
                          digits=dp.get_precision('Product Price'),
                          store=True)
    purchase_price = fields.Float(compute='_product_coeff',string="Cost",
                                  digits=dp.get_precision("Product Price"),
                                  store=True
                                  )
    purchase_price_net = fields.Float(compute='_product_coeff',string="Net Cost",
                                  digits=dp.get_precision("Product Price"),
                                  store=True)
    line_ref_cost =fields.Float(compute='_product_coeff',string="Ref Cost",
                                  digits=dp.get_precision("Product Price"),
                                  store=True)
    line_cost =fields.Float(compute='_product_coeff',string="Product Cost",
                                  digits=dp.get_precision("Product Price"),
                                  store=True)


    @api.multi
    def cron_update_cost_line(self):
        lines = self.search([("line_ref_cost", "=", 0)])
        lines.update_line_cost()
        
        
    @api.multi
    def update_line_cost(self):
        for line in self:
            if line.product_id.type != 'product':
                # 75 % del precio venta según correo de Juan el 29/09/20
                line.line_ref_cost = line.price_subtotal * 0.75                    
                line.line_cost = line.price_subtotal * 0.75
            else:
                if line.product_id.last_purchase_price_fixed:
                    ref_cost_price = line.product_id.reference_cost 
                    ref_cost_price = line._compute_cost_price(ref_cost_price)
                    cost_price = line.product_id.last_purchase_price_fixed or \
                         line.product_id.standard_price
                    cost_price = line._compute_cost_price(cost_price)
                    line.line_ref_cost = ref_cost_price * line.product_uom_qty
                    line.line_cost = cost_price * line.product_uom_qty
                    
                


    #@profile
    def _compute_cost_price(self, price):
        frm_cur = self.env.user.company_id.currency_id
        to_cur = self.order_id.pricelist_id.currency_id
        
        if self.product_uom != self.product_id.uom_id:
            price = self.product_id.uom_id._compute_price(
                price, self.product_uom)
        if frm_cur != to_cur:
            price = frm_cur._convert(
                price, to_cur,
                self.order_id.company_id or self.env.user.company_id,
                self.order_id.date_order or fields.Date.today(), round=False)
        return price

    #@profile
    @api.depends('product_id', 'product_uom_qty',
                 'price_unit', 'price_subtotal')
    def _product_margin(self):
        for line in self:
            if line.product_id.type != 'product':
                line.margin = line.price_subtotal * 0.25
            else:
                # currency = line.order_id.pricelist_id.currency_id
                purchase_price = line.product_id.reference_cost or \
                         line.product_id.standard_price
                price = line._compute_cost_price(purchase_price)
                
                line.margin = line.price_subtotal - \
                              (price * line.product_uom_qty)
                
    
    @api.depends('product_id', 'product_uom_qty',
                 'price_unit', 'price_subtotal')
    def _product_coeff(self):
        for line in self:
            if line.product_id.type != 'product':
                # 75 % del precio venta según correo de Juan el 29/09/20
                line.line_ref_cost = line.price_subtotal * 0.75                    
                line.line_cost = line.price_subtotal * 0.75
            else:
                # currency = line.order_id.pricelist_id.currency_id
                ref_cost_price = line.product_id.reference_cost or \
                         line.product_id.standard_price
                ref_cost_price = line._compute_cost_price(ref_cost_price)
                
                cost_price = line.product_id.last_purchase_price_fixed or \
                         line.product_id.standard_price
                cost_price = line._compute_cost_price(cost_price)

                line.line_ref_cost = ref_cost_price * line.product_uom_qty
                line.line_cost = cost_price * line.product_uom_qty    
            line.purchase_price = ref_cost_price
            line.purchase_price_net = cost_price
