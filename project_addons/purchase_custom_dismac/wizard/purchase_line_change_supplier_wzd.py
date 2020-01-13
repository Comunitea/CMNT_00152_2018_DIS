# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp

DOMAIN_STATES = ["draft"]


class PLPCLine(models.TransientModel):
    _name = "plpc.line"

    @api.multi
    def get_same_partner(self):
        for line in self:
            line.same_partner = line.partner_id == line.wzd_id.partner_id

    wzd_id = fields.Many2one("purchase.line.partner.change")
    purchase_line_id = fields.Many2one("purchase.order.line")
    partner_id = fields.Many2one(related="purchase_line_id.partner_id")
    product_id = fields.Many2one(related="purchase_line_id.product_id")
    product_qty = fields.Float(related="purchase_line_id.product_qty")
    product_uom = fields.Many2one(related="purchase_line_id.product_uom")
    price_unit = fields.Float(related="purchase_line_id.price_unit")
    partner_price_unit = fields.Float(
        string="Unit Price",
        required=True,
        digits=dp.get_precision("Product Price"),
    )
    same_partner = fields.Boolean(compute=get_same_partner)


class PurchaseLinePartnerChangeWzd(models.TransientModel):

    _name = "purchase.line.partner.change"

    partner_id = fields.Many2one(
        "res.partner",
        "Vendor",
        domain=[("supplier", "=", True)],
        required=True,
        help="Vendor of this product",
    )
    show_price = fields.Boolean(default=False)
    show_apply_partner = fields.Boolean(default=False)
    show_apply_order = fields.Boolean(default=False)

    initial_amount = fields.Float(
        string="Inicial", digits=dp.get_precision("Product Price")
    )
    partner_amount = fields.Float(
        string="Propuesto", digits=dp.get_precision("Product Price")
    )
    line_ids = fields.Many2many("plpc.line")
    partner_ids = fields.Many2many("res.partner")
    purchase_order_id = fields.Many2one(
        "purchase.order", "Pedido de compra encontrado"
    )

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        self.show_apply_partner = True
        self.show_apply_order = False

    def get_vals(self, pol):
        return {
            "selected": True,
            "purchase_line_id": pol.id,
            "purchase_id": pol.order_id.id,
            "partner_id": pol.partner_id.id,
            "product_id": pol.product_id.id,
            "product_qty": pol.product_qty,
            "product_uom": pol.product_uom.id,
            "price_unit": pol.price_unit,
            "partner_price_unit": 0.00,
        }

    @api.model
    def default_get(self, field_list):

        res = super(PurchaseLinePartnerChangeWzd, self).default_get(field_list)
        line_ids = self.env["plpc.line"]
        active_ids = self._context.get("active_ids", False)

        if active_ids:
            pol_ids = (
                self.env["purchase.order.line"]
                .browse(active_ids)
                .filtered(lambda x: x.state == "draft")
            )
            for pol in pol_ids:
                new_line = line_ids.create(self.get_vals(pol))
                line_ids |= new_line
        partner_ids = line_ids.mapped("partner_id")
        domain = [("product_id", "in", line_ids.mapped("product_id").ids)]
        suplier_ids = (
            self.env["product.supplierinfo"].search(domain).mapped("name")
        )
        partner_ids |= suplier_ids

        if line_ids:
            res["line_ids"] = [(6, 0, line_ids.ids)]
            res["partner_ids"] = [(6, 0, partner_ids.ids)]
        return res

    @api.multi
    def apply_partner(self):
        if self.partner_id:
            po_vals = {"partner_id": self.partner_id.id}
            po = self.env["purchase.order"].new(po_vals)

            for line in self.line_ids:
                pol_val = {
                    "product_qty": line.product_qty,
                    "name": line.product_id.display_name,
                    "partner_id": self.partner_id.id,
                    "product_id": line.product_id.id,
                }
                new_pol = po.order_line.new(pol_val)
                new_pol.onchange_product_id()
                new_pol.product_qty = line.product_qty
                new_pol._onchange_quantity()
                line.partner_price_unit = new_pol.price_unit

            self.show_price = True
        else:
            self.show_price = False
            self.line_ids.write({"partner_price_unit": 0.00})

        action = self.env.ref(
            "purchase_custom_dismac.action_purchase_line_partner_change_form"
        )
        vals = action.read()[0]
        vals["res_id"] = self.id
        self.show_apply_partner = False
        self.show_apply_order = True

        return vals

    @api.multi
    def apply_order(self):
        if self.partner_id:
            po_vals = {"partner_id": self.partner_id.id}
            po = self.env["purchase.order"].create(po_vals)

            for line in self.line_ids.filtered(
                lambda x: x.partner_id in self.partner_ids
                and x.partner_price_unit > 0
            ):
                pol_val = {
                    "product_qty": line.product_qty,
                    "name": line.product_id.display_name,
                    "partner_id": self.partner_id.id,
                    "product_id": line.product_id.id,
                    "order_id": po.id,
                }
                new_pol = po.order_line.new(pol_val)

                new_pol.onchange_product_id()
                new_pol.product_qty = line.product_qty
                new_pol._onchange_quantity()
                new_pol_vals = new_pol._convert_to_write(new_pol._cache)
                po.order_line.create(new_pol_vals)
                line.purchase_line_id.unlink()
