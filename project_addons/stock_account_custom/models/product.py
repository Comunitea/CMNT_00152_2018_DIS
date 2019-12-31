# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ProductPriceRatio(models.Model):

    _name = "product.price.ratio"

    name = fields.Char("Name")
    purchase_ratio = fields.Float(
        "Purchase ratio",
        help="Ratio to get reference cost from pricelist_cost",
        digits=(16, 4),
    )


class ProductProduct(models.Model):

    _inherit = "product.product"

    real_stock_cost = fields.Float(
        "Real stock cost",
        compute="_get_compute_custom_costs",
        digits=dp.get_precision("Product Price"),
        groups="stock_account_custom.group_cost_manager",
        help="Stock value / Qty",
    )
    real_stock_cost_fixed = fields.Float(
        "Fixed real stock cost",
        compute="_get_compute_custom_costs",
        digits=dp.get_precision("Product Price"),
        groups="stock_account_custom.group_cost_manager",
        help="Stock value / Qty (without special purchases)",
    )
    pricelist_cost = fields.Float(
        "Price list cost",
        digits=dp.get_precision("Product Price"),
        groups="stock_account_custom.group_cost_manager",
        help="Cost price used in pricelist (Last purchase cost manually "
        "frozen",
    )
    reference_cost = fields.Float(
        "Reference cost",
        compute="_get_compute_custom_costs",
        digits=dp.get_precision("Product Price"),
        help="Cost price (reference)",
    )
    last_purchase_price_fixed = fields.Float(
        string="Last Purchase Price Fixed",
        compute="_compute_last_purchase_fixed",
        digits=dp.get_precision("Product Price"),
    )
    force_purchase_price_fixed = fields.Boolean(
        "Force Last Purchase Price Fixed", default=False
    )
    last_purchase_price_fixed_alternative = fields.Float(
        string="Last Purchase Price Fixed Alternative",
        digits=dp.get_precision("Product Price"),
    )

    @api.model
    def update_pricelist_cost(self):
        for product in self:
            if product.cost_method_calc == "last_cost":
                product.pricelist_cost = product.last_purchase_price_fixed
            if product.cost_method_calc == "formula":
                product.pricelist_cost = (
                    product.cost_method_product_id.last_purchase_price_fixed
                    * product.cost_method_ratio
                )
            if product.cost_method_calc == "max":
                product.pricelist_cost = product.get_max_in_period()

    @api.multi
    def get_max_in_period(self):
        PurchaseOrderLine = self.env["purchase.order.line"]

        ref_date = datetime.today() - relativedelta(months=self.period_max_cost)
        lines = PurchaseOrderLine.search(
            [
                ("product_id", "=", self.id),
                ("state", "in", ["purchase", "done"]),
                (
                    "order_id.date_order",
                    ">=",
                    fields.Datetime.to_string(ref_date),
                ),
            ]
        )
        inv_lines = lines.mapped("invoice_lines")
        pur_prices = lines.mapped("price_unit")
        inv_prices = inv_lines.mapped("price_unit")
        product_price = max(pur_prices + inv_prices)
        return product_price

    def _get_compute_custom_costs_with_context(self, ctx):
        qty_at_date = self.qty_at_date
        product = self.with_context(ctx)
        candidates = product._get_fifo_candidates_in_move()
        qty_remaining = sum(x.remaining_qty for x in candidates)
        qty = qty_at_date - qty_remaining
        if qty:
            res = product.stock_value / qty
        else:
            res = product.real_stock_cost
        return res

    @api.multi
    def _get_compute_custom_costs(self):
        # Real stock_cost: Todos los movimientos
        for product in self:
            if product.qty_at_date:
                product.real_stock_cost = (
                    product.stock_value / product.qty_at_date
                )
        # Fixed real stock_cost: Solo los movimientos con exclude_compute_cost = False
        ctx = self._context.copy()
        ctx.update(exclude_compute_cost=True)
        for product in self:
            product.real_stock_cost_fixed = product._get_compute_custom_costs_with_context(
                ctx
            )
            if product.product_tmpl_id.cost_ratio_id:
                product.reference_cost = (
                    product.last_purchase_price_fixed
                    * product.product_tmpl_id.cost_ratio_id.purchase_ratio
                    or 1.0
                )
            else:
                product.reference_cost = product.last_purchase_price_fixed

    @api.multi
    def price_compute(
        self, price_type, uom=False, currency=False, company=False
    ):

        if price_type != "pricelist_cost":
            return super().price_compute(
                price_type=price_type,
                uom=uom,
                currency=currency,
                company=company,
            )

        ##COPIA DE price_compute PERO DOY POR HECHO QUE ES PARA reference_cost
        if not uom and self._context.get("uom"):
            uom = self.env["uom.uom"].browse(self._context["uom"])
        if not currency and self._context.get("currency"):
            currency = self.env["res.currency"].browse(
                self._context["currency"]
            )
        products = self.with_context(
            force_company=company
            and company.id
            or self._context.get("force_company", self.env.user.company_id.id)
        ).sudo()
        prices = dict.fromkeys(self.ids, 0.0)
        for product in products:
            prices[product.id] = product[price_type] or 0.0
            if uom:
                prices[product.id] = product.uom_id._compute_price(
                    prices[product.id], uom
                )
            # Convert from current user company currency to asked one
            # This is right cause a field cannot be in more than one currency
            if currency:
                prices[product.id] = product.currency_id.compute(
                    prices[product.id], currency
                )

        return prices

    @api.multi
    def _compute_last_purchase_fixed(self):
        """ Get last purchase price, last purchase date and last supplier """
        PurchaseOrderLine = self.env["purchase.order.line"]
        for product in self:
            if product.force_purchase_price_fixed:
                product.last_purchase_price_fixed = (
                    product.last_purchase_price_fixed_alternative
                )
            else:
                lines = PurchaseOrderLine.search(
                    [
                        ("product_id", "=", product.id),
                        ("state", "in", ["purchase", "done"]),
                        ("order_id.exclude_compute_cost", "<>", True),
                    ]
                ).sorted(key=lambda l: l.order_id.date_order, reverse=True)
                inv_lines = lines[:1].invoice_lines.sorted(
                    key=lambda l: l.invoice_id.date_invoice, reverse=True
                )
                if inv_lines:
                    lpp = inv_lines[:1].price_unit
                    uom_id = inv_lines[:1].uom_id
                else:
                    lpp = lines[:1].price_unit
                    uom_id = lines[:1].product_uom
                if uom_id and uom_id.id != product.uom_id.id:
                    lpp = uom_id._compute_price(lpp, product.uom_id)
                if lpp == 0 and product.last_purchase_price != 0:
                    lpp = product.last_purchase_price
                product.last_purchase_price_fixed = lpp


class ProductTemplate(models.Model):

    _inherit = "product.template"

    cost_ratio_id = fields.Many2one(
        "product.price.ratio",
        "Price ratio",
        company_dependent=True,
        help="Product ranking to get reference cost and product price",
    )
    stock_value = fields.Float("Value", compute="_compute_reference_cost")
    qty_at_date = fields.Float("Quantity", compute="_compute_reference_cost")
    reference_cost = fields.Float(
        "Reference cost",
        compute="_compute_reference_cost",
        digits=dp.get_precision("Product Price"),
        groups="stock_account_custom.group_cost_manager",
        help="Cost price for salesman users (Fixed real stock cost fixed by ratio)",
    )
    pricelist_cost = fields.Float(
        "Pricelist cost",
        digits=dp.get_precision("Product Price"),
        groups="stock_account_custom.group_cost_manager",
        help="Cost price used in pricelist (Fixed real stock cost manually frozen",
    )
    real_stock_cost = fields.Float(
        "Real stock cost",
        compute="_compute_reference_cost",
        digits=dp.get_precision("Product Price"),
        groups="stock_account_custom.group_cost_manager",
        help="Stock value / Qty",
    )
    real_stock_cost_fixed = fields.Float(
        "Fixed real stock cost",
        compute="_compute_reference_cost",
        digits=dp.get_precision("Product Price"),
        groups="stock_account_custom.group_cost_manager",
        help="Stock value / Qty (without special purchases)",
    )
    cost_method_calc = fields.Selection(
        [
            ("last_cost", "Last Cost"),
            ("manual", "Manual"),
            ("formula", "Formula"),
            ("max", "Max in Period"),
        ],
        "Calculation method",
        default="last_cost",
        required=True,
        help="Calculation method for Pricelist Cost",
    )
    period_max_cost = fields.Integer("Period (Months)")
    cost_method_product_id = fields.Many2one("product.product", "Cost Product")
    cost_method_ratio = fields.Float("Ratio", digits=(16, 4), default="1")

    @api.depends("product_variant_ids", "product_variant_ids.reference_cost")
    def _compute_reference_cost(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1
        )

        for template in unique_variants:
            template.reference_cost = (
                template.product_variant_ids.reference_cost
            )
            template.pricelist_cost = (
                template.product_variant_ids.pricelist_cost
            )
            template.real_stock_cost = (
                template.product_variant_ids.real_stock_cost
            )
            # template.real_stock_cost_fixed =
            # template.product_variant_ids.real_stock_cost_fixed

            template.stock_value = template.product_variant_ids.stock_value
            template.qty_at_date = template.product_variant_ids.qty_at_date

        for template in self - unique_variants:
            n_v = len(template.product_variant_ids) or 1
            pricelist_cost = sum(
                x.pricelist_cost for x in template.product_variant_ids
            )
            reference_cost = sum(
                x.reference_cost for x in template.product_variant_ids
            )
            real_stock_cost = sum(
                x.real_stock_cost for x in template.product_variant_ids
            )
            # real_stock_cost_fixed = sum(x.fixed_real_stock_cost for x in
            # template.product_variant_ids)
            stock_value = sum(
                x.stock_value for x in template.product_variant_ids
            )
            qty_at_date = sum(
                x.qty_at_date for x in template.product_variant_ids
            )

            template.pricelist_cost = pricelist_cost / n_v
            template.reference_cost = reference_cost / n_v
            template.real_stock_cost = real_stock_cost / n_v
            # template.real_stock_cost_fixed = real_stock_cost_fixed / n_v
            template.stock_value = stock_value / n_v
            template.qty_at_date = qty_at_date / n_v

    @api.multi
    def price_compute(
        self, price_type, uom=False, currency=False, company=False
    ):

        if price_type != "pricelist_cost":
            return super().price_compute(
                price_type=price_type,
                uom=uom,
                currency=currency,
                company=company,
            )

        if not uom and self._context.get("uom"):
            uom = self.env["uom.uom"].browse(self._context["uom"])
        if not currency and self._context.get("currency"):
            currency = self.env["res.currency"].browse(
                self._context["currency"]
            )

        templates = self.with_context(
            force_company=company
            and company.id
            or self._context.get("force_company", self.env.user.company_id.id)
        ).sudo()
        prices = dict.fromkeys(self.ids, 0.0)
        for template in templates:
            prices[template.id] = template[price_type] or 0.0
            if uom:
                prices[template.id] = template.uom_id._compute_price(
                    prices[template.id], uom
                )
            if currency:
                prices[template.id] = template.currency_id.compute(
                    prices[template.id], currency
                )

        return prices
