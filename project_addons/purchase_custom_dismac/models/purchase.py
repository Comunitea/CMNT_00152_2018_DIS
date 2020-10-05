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


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    import_qty_delivered = fields.Float("Imported qty delivered", default=0)
    new_partner_id = fields.Many2one("res.partner", "New partner")
    product_stock_available = fields.Float(
        "available qty", related="product_id.qty_available"
    )
    product_virtual_available = fields.Float(
        "virtual available qty", related="product_id.virtual_available"
    )
    product_categ_id = fields.Many2one(
        "product.category", "Category", related="product_id.categ_id"
    )
    to_deliver_qty = fields.Float(compute="_compute_to_deliver_qty")
    last_60_days_sales = fields.Float(related="product_id.last_60_days_sales")
    min_max_reordering = fields.Char('Min/Max', compute="_compute_max_min")
    location_id = fields.Many2one('stock.location', 'Ubicación de stock', store = False)

    @api.onchange('new_partner_id')
    def _onchange_new_partner(self):
        self.discount = self.new_partner_id.default_supplierinfo_discount
        psinfo = self.env['product.supplierinfo'].search(
            [('name', '=', self.new_partner_id.id),
             ('product_id', '=', self.product_id.id)], limit=1)
        if psinfo:
            self.price_unit = psinfo[0].price

    def _compute_max_min(self):
        for line in self:
            if line.product_id.nbr_reordering_rules == 1:
                line.min_max_reordering = \
                    str(line.product_id.reordering_min_qty) + "/" +\
                    str(line.product_id.reordering_max_qty)
            else:
                line.min_max_reordering = "--/--"

    def _compute_to_deliver_qty(self):
        ## Todo revisar con Jose Luis que movimientos se tienen en cuenta.
        domain = [
                  ('location_id.usage', '=', 'internal'),
                  ('location_dest_id.usage', '!=', 'internal'),
                  ('state', 'in', ('partially_available', 'assigned', 'confirmed')),
                  ('product_id', 'in', self.mapped('product_id').ids)]

        if self._context.get('location'):
            domain += [('location_id', 'child_of', self._context.get('location'))]

        res = self.env['stock.move'].read_group(domain, ['product_uom_qty'], ['product_id'])
        qties = {}
        for x in res:
            qties[x['product_id'][0]] = x['product_uom_qty']

        for line in self:
            product_id = line.product_id.id
            if product_id in qties.keys():
                line.to_deliver_qty = qties[line.product_id.id]
            else:
                line.to_deliver_qty = 0
        return

        for line in self:
            self.env.cr.execute(
                """
                    SELECT SUM(qty_pending)
                    FROM sale_order_line
                    WHERE state not in ('draft','sent', 'cancel') AND
                    product_id={}
                """.format(
                    line.product_id.id
                )
            )
            result = self.env.cr.fetchone()
            if result and result[0]:
                line.to_deliver_qty = result[0]
            else:
                line.to_deliver_qty = 0

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking=picking)
        if self.import_qty_delivered > 0:
            for val in res:
                qty = val["product_uom_qty"] - self.import_qty_delivered
                val.update(product_uom_qty=qty)
        return res

    def _update_received_qty(self):
        res = super()._update_received_qty()
        for line in self:
            line.qty_received += line.import_qty_delivered
        return res


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
