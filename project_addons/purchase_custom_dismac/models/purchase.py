# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from odoo.tools.misc import formatLang


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.depends("picking_ids.state", "picking_ids.supplier_ref")
    def _get_supplier_pick_refs(self):
        for purchase in self:
            refs = []
            for pick in purchase.picking_ids:
                if (
                    pick.supplier_ref
                    and pick.state == "done"
                    and pick.supplier_ref not in refs
                ):
                    refs.append(pick.supplier_ref)
            if refs:
                purchase.supplier_picking_ref = " // ".join(refs)
            else:
                purchase.supplier_picking_ref = ""

    shipment_count_ = fields.Integer(
        "Incoming Shipments", compute="_count_ship", store=True
    )
    carrier = fields.Many2one("delivery.carrier", "Carrier")
    supplier_picking_ref = fields.Text(
        "Supplier picking refs.", store=True, compute="_get_supplier_pick_refs"
    )
    needed_for_free_delivery = fields.Float(
        "Amount needed to get free delivery amount.",
        compute="_check_min_delivery_amount",
        store=True,
    )

    @api.depends("picking_ids.state")
    def _count_ship(self):
        for po in self:
            po.shipment_count_ = len(
                [x.id for x in po.picking_ids if x.state not in ["cancel"]]
            )

    @api.multi
    @api.depends("order_line.date_planned", "date_order")
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

    @api.multi
    @api.depends("amount_total")
    def _check_min_delivery_amount(self):
        for order in self:
            order.needed_for_free_delivery = (
                order.partner_id.min_amount_for_free_delivery
                - order.amount_total
            )


class PurchaseBillUnion(models.Model):
    _inherit = "purchase.bill.union"

    def name_get(self):
        result = []
        for doc in self:
            name = doc.name or ""
            if doc.reference:
                name += " - " + doc.reference
            amount = doc.amount
            if (
                doc.purchase_order_id
                and doc.purchase_order_id.invoice_status == "no"
            ):
                amount = 0.0
            name += ": " + formatLang(
                self.env, amount, monetary=True, currency_obj=doc.currency_id
            )
            if doc.purchase_order_id.supplier_picking_ref:
                name += ": " + doc.purchase_order_id.supplier_picking_ref
            result.append((doc.id, name))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        purchases = (
            self.env["purchase.order"]
            .search([("supplier_picking_ref", operator, name)])
            ._ids
        )
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                ("name", operator, name),
                ("reference", operator, name),
                ("purchase_order_id", "in", purchases),
            ]
        pos = self.search(domain + args, limit=limit)
        return pos.name_get()
