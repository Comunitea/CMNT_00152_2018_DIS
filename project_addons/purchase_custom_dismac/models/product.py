# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from datetime import timedelta


class ProductProduct(models.Model):
    _inherit = "product.product"

    last_60_days_sales = fields.Float()


    ## Sobrescribe función para poder considerar los descuentos en las lineas de comopra
    @api.multi
    def set_product_last_purchase(self, order_id=False):
        """ Get last purchase price, last purchase date and last supplier """
        PurchaseOrderLine = self.env['purchase.order.line']
        if not self.check_access_rights('write', raise_exception=False):
            return
        for product in self:
            date_order = False
            price_unit_uom = 0.0
            last_supplier = False

            # Check if Order ID was passed, to speed up the search
            if order_id:
                lines = PurchaseOrderLine.search([
                    ('order_id', '=', order_id),
                    ('product_id', '=', product.id)], limit=1)
            else:
                lines = PurchaseOrderLine.search(
                    [('product_id', '=', product.id),
                     ('state', 'in', ['purchase', 'done'])]).sorted(
                    key=lambda l: l.order_id.date_order, reverse=True)

            if lines:
                # Get most recent Purchase Order Line
                last_line = lines[:1]

                date_order = last_line.order_id.date_order
                # Compute Price Unit in the Product base UoM
                price_unit = last_line.price_unit * (1-last_line.discount/100)
                price_unit_uom = product.uom_id._compute_quantity(
                    price_unit, last_line.product_uom)
                last_supplier = last_line.order_id.partner_id

            # Assign values to record
            product.write({
                "last_purchase_date": date_order,
                "last_purchase_price": price_unit_uom,
                "last_supplier_id": last_supplier.id
                if last_supplier else False,
            })
            # Set related product template values
            product.product_tmpl_id.set_product_template_last_purchase(
                date_order, price_unit_uom, last_supplier)


    @api.model
    def compute_last_60_days_sales(self, products=False):
        sixty_days_ago = fields.Datetime.now() + timedelta(days=-60)
        if not products:
            products = self.search([("type", "!=", "service")])
        for product in products:
            sale_lines = self.env["sale.order.line"].search(
                [
                    ("product_id", "=", product.id),
                    ("order_id.date_order", ">=", sixty_days_ago),
                    ("state", "not in", ('draft', 'sent', 'cancel')),
                ]
            )
            product.last_60_days_sales = sum(
                sale_lines.mapped("product_uom_qty")
            )

    def button_compute_last_60_days_sales(self):
        self.compute_last_60_days_sales(self)

    def get_unreceived_items(self):
        model_data = self.env["ir.model.data"]

        tree_view = model_data.get_object_reference(
            "purchase_custom_dismac", "purchase_custom_tree"
        )
        search_view = model_data.get_object_reference(
            "purchase_custom_dismac", "purchase_custom_search"
        )
        domain = [("product_id", "=", self.id)]
        value = {}
        for call in self:
            value = {
                "name": _("Purchase order lines"),
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "purchase.order.line",
                "views": [(tree_view and tree_view[1] or False, "tree")],
                "type": "ir.actions.act_window",
                "domain": domain,
                "search_view_id": search_view and search_view[1] or False,
                "context": {"search_default_draft": 1},
            }
        return value
