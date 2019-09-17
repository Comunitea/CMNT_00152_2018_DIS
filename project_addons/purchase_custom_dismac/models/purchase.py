# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.depends('picking_ids.state', 'picking_ids.supplier_ref')
    def _get_supplier_pick_refs(self):
        for purchase in self:
            refs = []
            for pick in purchase.picking_ids:
                if pick.supplier_ref and pick.state == 'done' \
                        and pick.supplier_ref not in refs:
                    refs.append(pick.supplier_ref)
            if refs:
                purchase.supplier_picking_ref = " // ".join(refs)

    shipment_count_ = fields.Integer('Incoming Shipments',
                                     compute='_count_ship', store=True)
    carrier = fields.Many2one('delivery.carrier', 'Carrier')
    supplier_picking_ref = fields.Text("Supplier picking refs.", store=True,
                                       compute="_get_supplier_pick_refs")
    #needed_for_min_amount = fields.Float('Amount needed to achieve the min. delivery amount.', compute="_check_min_purchase_amount", store=True)
    needed_for_free_delivery = fields.Float('Amount needed to get free delivery amount.', compute="_check_min_delivery_amount", store=True)

    @api.multi
    @api.depends('name', 'partner_ref')
    def name_get(self):
        result = []
        for po in self:
            name = po.name
            if po.partner_ref:
                name += ' (' + po.partner_ref + ')'
            if self.env.context.get('show_total_amount') and po.amount_total:
                name += ': ' + formatLang(self.env, po.amount_total,
                                          currency_obj=po.currency_id)
                if po.supplier_picking_ref:
                    name += ': ' + po.supplier_picking_ref
            result.append((po.id, name))
        return result

    @api.depends('picking_ids.state')
    def _count_ship(self):
        for po in self:
            po.shipment_count_ = len([x.id for x in po.picking_ids
                                      if x.state not in ['cancel']])

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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name),
                      ('partner_ref', operator, name),
                      ('supplier_picking_ref', operator, name)]
        pos = self.search(domain + args, limit=limit)
        return pos.name_get()