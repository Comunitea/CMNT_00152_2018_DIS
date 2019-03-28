# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    #needed_for_min_amount = fields.Float('Amount needed to achieve the min. delivery amount.', compute="_check_min_purchase_amount", store=True)
    needed_for_free_delivery = fields.Float('Amount needed to get free delivery amount.', compute="_check_min_delivery_amount", store=True)

    @api.multi
    @api.depends('order_line.date_planned', 'date_order')
    def _compute_date_planned(self):
        for order in self:
            min_date = False
            for line in order.order_line:
                if not min_date or line.date_planned < min_date:
                    min_date = line.date_planned
            if min_date:
                order.date_planned = min_date
            else:
                order.date_planned = order.date_order 
    
    # @api.multi
    # @api.depends('amount_total')
    # def _check_min_purchase_amount(self):
    #     for order in self:
    #         order.needed_for_min_amount = order.partner_id.min_amount_to_serve - order.amount_total
    
    @api.multi
    @api.depends('amount_total')
    def _check_min_delivery_amount(self):
        for order in self:
            order.needed_for_free_delivery = order.partner_id.min_amount_for_free_delivery - order.amount_total
#
# class PurchaseOrderLine(models.Model):
#     _inherit = "purchase.order.line"
#
#     qty_to_receive = fields.Float('Quantity left to recieve', compute="_update_quantity_left_to_recieve", store=True)
#
#     @api.multi
#     @api.depends('product_qty', 'qty_received')
#     def _update_quantity_left_to_recieve(self):
#         for var in self:
#             var.qty_to_receive = var.product_qty - var.qty_received