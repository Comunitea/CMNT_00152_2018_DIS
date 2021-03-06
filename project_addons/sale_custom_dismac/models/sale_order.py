# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from .res_partner import PROCUREMENT_PRIORITIES
from odoo.tools import float_is_zero
from odoo.tools import float_compare, pycompat
from datetime import datetime
from odoo.addons import decimal_precision as dp

class SaleOrder(models.Model):

    _inherit = "sale.order"

    # @api.multi
    # @api.depends('order_line')
    # def _compute_sale_order_lines_count(self):
    #     for order in self:
    #         order.order_lines_count = len(order.order_line)

    # order_lines_count = fields.Integer(
    #     'Line count', compute='_compute_sale_order_lines_count')
    pending_review = fields.Boolean()
    need_approval = fields.Boolean(
        related="type_id.need_approval", readonly=True
    )
    priority = fields.Selection(PROCUREMENT_PRIORITIES, "Priority", default="1")
    pending_invoice_amount = fields.Float(
        compute="_compute_pending_invoice_amount",
        search="_search_pending_invoice_amount",
    )
    project_reference = fields.Char("Project Reference")
    transmit_method_id = fields.Many2one(
        related="partner_invoice_id.customer_invoice_transmit_method_id",
        string="Transmission Method",
        store=True,
    )
    commercial_partner_id = fields.Many2one(
        related="partner_id.commercial_partner_id"
    )
    order_line_count = fields.Integer(
        "# Líneas", compute="_get_sale_line_count", store=True
    )
    commercial_partner_user_id = fields.Many2one('res.users', 
        related= 'commercial_partner_id.user_id', 
        store=True,
        string='Commercial partner Salesperson')

    default_location_id = fields.Many2one('stock.location', 'Ubicación de abastecimiento')

    @api.multi
    @api.depends("order_line")
    def _get_sale_line_count(self):
        for order in self:
            order.order_line_count = len(order.order_line)

    # Por compatibilidad entre sale_order_revision y sale_order_type
    @api.multi
    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
        if default.get("name", "/") == "/" and self.type_id:
            if self.type_id.sequence_id:
                default["name"] = self.type_id.sequence_id.next_by_id()
                default["unrevisioned_name"] = default["name"]
        return super(SaleOrder, self).copy(default=default)

    def _compute_pending_invoice_amount(self):
        for order in self:
            order_amount = 0
            for line in order.order_line:
                if line.qty_to_invoice_on_date:
                    order_amount += (
                        line.qty_to_invoice_on_date
                        * line.price_unit
                        * (1 - line.discount / 100)
                    )
            order.pending_invoice_amount = order_amount

    @api.multi
    def action_confirm(self):
        """
        Check if order requires client_order_ref
        """
        for order in self:
            if (
                order.partner_id.require_num_order
                and not order.client_order_ref
            ):
                msg = _(
                    "The customer for this order requires a customer \
                        reference number"
                )
                raise UserError(msg)
            if any(order.mapped("order_line.product_id.review_order")):
                order.pending_review = True
            else:
                order.pending_review = False
        res = super().action_confirm()
        return res

    @api.multi
    def action_draft(self):
        self.write({"active": True})
        return super(SaleOrder, self).action_draft()

    def set_user_id(self):
        if self.type_id.use_partner_agent:
            user = self.partner_id.user_id
            if not self.partner_id.is_company and not user:
                user = self.partner_id.commercial_partner_id.user_id
            self.user_id = user
        else:
            self.user_id = self.env.uid

    @api.onchange('partner_shipping_id')
    def _onchange_partner_shipping_id(self):
        self.default_location_id = self.partner_id.default_location_id
        res = super()._onchange_partner_shipping_id()

        return res

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        """
        Look at the partner for changing the invoice policy
        """
        res = super().onchange_partner_id()
        val = {}
        if self.partner_id:
            if self.partner_id.whole_orders:
                val["picking_policy"] = "one"
            val["priority"] = self.partner_id.priority
        self.update(val)
        self.set_user_id()
        return res

    @api.onchange("type_id")
    def onchange_type_id_user_id(self):
        self.set_user_id()

    # @api.multi
    # def action_view_order_lines(self):
    #     self.ensure_one()

    #     # model_data = self.env['ir.model.data']
    #     # tree_view = model_data.get_object_reference(
    #     #     'sale_custom_dismac', 'sale_order_line_tree_view')
    #     tree_view_name = 'sale_custom_dismac.sale_order_line_tree_view'
    #     tree_view = self.env.ref(tree_view_name)

    #     action = self.env.ref(
    #         'sale_custom_dismac.sale_order_line_tree_view_action').read()[0]

    #     action['views'] = {
    #         (tree_view and tree_view.id or False, 'tree')}

    #     action['domain'] = [('order_id', '=', self.id)]

    #     action['context'] = {
    #         'default_order_id': self.id,
    #         'partner_id': self.partner_id.id,
    #         'pricelist': self.pricelist_id,
    #         'company_id': self.company_id.id,
    #         'type_id': self.type_id.id,
    #     }
    #     action.update(
    #         {'tax_id': {'domain': [('type_tax_use', '=', 'sale'),
    #                                ('company_id', '=', self.company_id)]}}
    #          )

    #     return action

    invoice_until = fields.Date(
        store=False, search=lambda operator, operand, vals: []
    )
    delivery_until = fields.Date(
        store=False, search=lambda operator, operand, vals: []
    )

    def _compute_has_invoiceable_lines(self):
        for order in self:
            if self.env["sale.order.line"].search(
                [
                    ("qty_to_invoice_on_date", ">", 0),
                    ("order_id", "=", order.id),
                ]
            ):
                order.has_invoiceable_lines = True
            else:
                order.has_invoiceable_lines = False

    def _search_has_invoiceable_lines(self, operator, operand):
        if self._context.get("invoice_until"):
            query = """
            SELECT DISTINCT sol.order_id
            FROM sale_order_line_delivery soly
                RIGHT JOIN sale_order_line sol on soly.line_id = sol.id
            WHERE sol.invoice_status = 'to invoice'
                and sol.company_id = %(company_id)s
                and soly.delivery_date <= %(delivery_date)s
            GROUP BY soly.line_id, sol.order_id
            HAVING SUM(
                CASE 
                WHEN soly.quantity is Not Null THEN soly.quantity
                ELSE 0
                END)
                + SUM(
                CASE 
                WHEN picking_imported is not Null THEN sol.import_qty_delivered
                ELSE 0
                END)
                - SUM(sol.qty_invoiced) > 0
            """
            params = {
                "company_id": self.env.user.company_id.id,
                "delivery_date": self._context.get("invoice_until"),
            }
            self.env.cr.execute(query, params)
            results = self.env.cr.fetchall()
            if results:
                return [("id", "in", [x[0] for x in results])]
            return [("id", "in", [])]
        else:
            return [("invoice_status", "=", "to invoice")]

    def _compute_sale_complete(self):
        for order in self:
            for line in order.order_line:
                if line.product_uom_quantity != line.qty_delivery_on_date:
                    order.sale_complete = False
                    continue

            order.sale_complete = True

    def _search_sale_complete(self, operator, operand):
        if self._context.get("invoice_until"):
            query = """
            SELECT DISTINCT sol.order_id
            FROM sale_order_line_delivery soly
                RIGHT JOIN sale_order_line sol on soly.line_id = sol.id
            WHERE
                sol.company_id = %(company_id)s

            GROUP BY soly.line_id, sol.order_id
            HAVING SUM(
                CASE WHEN soly.quantity is Null or soly.delivery_date > %(delivery_date)s
                    THEN 0
                ELSE soly.quantity
                END
            ) - SUM(sol.product_uom_qty) != 0
            """
            params = {
                "company_id": self.env.user.company_id.id,
                "delivery_date": self._context.get("invoice_until"),
            }
        else:
            query = """
            SELECT DISTINCT sol.order_id
            FROM sale_order_line_delivery soly
                RIGHT JOIN sale_order_line sol on soly.line_id = sol.id
            WHERE
                sol.company_id = %(company_id)s
            GROUP BY soly.line_id, sol.order_id
            HAVING SUM(
                CASE WHEN soly.quantity is Null
                    THEN 0
                ELSE soly.quantity
                END
            ) - SUM(sol.product_uom_qty) != 0
            """
            params = {"company_id": self.env.user.company_id.id}
        self.env.cr.execute(query, params)
        results = self.env.cr.fetchall()
        if results:
            if operand == True:
                return [("id", "not in", [x[0] for x in results])]
            else:
                return [("id", "in", [x[0] for x in results])]
        if operand == True:
            return [("id", "in", [])]
        else:
            return []

    has_invoiceable_lines = fields.Boolean(
        compute="_compute_has_invoiceable_lines",
        search="_search_has_invoiceable_lines",
    )

    sale_complete = fields.Boolean(
        compute="_compute_sale_complete", search="_search_sale_complete"
    )

    @api.model_cr
    def _register_hook(self):
        res = super()._register_hook()

        def new_action_invoice_create(self, grouped=False, final=False):
            """
            Create the invoice associated to the SO.
            :param grouped: if True, invoices are grouped by SO id. If False,
            invoices are grouped by (partner_invoice_id, currency)
            :param final: if True, refunds will be generated if necessary
            :returns: list of created invoices
            """
            if not hasattr(self, "_get_invoice_group_key"):
                return self.action_invoice_create_original(
                    grouped=grouped, final=final
                )
            invoices = {}
            references = {}

            # START HOOK
            # Take into account draft invoices when creating new ones
            self._get_draft_invoices(invoices, references)
            # END HOOK

            inv_obj = self.env["account.invoice"]
            precision = self.env["decimal.precision"].precision_get(
                "Product Unit of Measure"
            )

            # START HOOK
            # As now from the beginning there can be invoices related to that
            # order, instead of new invoices,
            # new lines are taking into account in
            # order to know whether there are invoice lines or not
            new_lines = False
            # END HOOK
            for order in self:
                # We only want to create sections that
                # have at least one invoiceable line
                pending_section = None
                for line in order.order_line.sorted(
                    key=lambda l: l.qty_to_invoice_on_date < 0
                ):
                    # Evitamos multiples llamada al campo
                    qty_to_invoice_date = line.qty_to_invoice_on_date 
                    if line.display_type == "line_section":
                        pending_section = line
                        continue
                    if float_is_zero(
                        qty_to_invoice_date, precision_digits=precision
                    ):
                        continue
                    # START HOOK
                    # Allow to check if a line should not be invoiced
                    if line._do_not_invoice():
                        continue
                    # END HOOK
                    # START HOOK
                    # Add more flexibility in grouping key fields
                    # WAS: group_key = order.id if grouped
                    # else (order.partner_invoice_id.id, order.currency_id.id)
                    group_key = (
                        order.id
                        if grouped
                        else self._get_invoice_group_line_key(line)
                    )
                    # 'invoice' must be always instantiated
                    # respecting the old logic
                    if group_key in invoices:
                        invoice = invoices[group_key]
                        # END HOOK
                    if group_key not in invoices:
                        inv_data = line._prepare_invoice()
                        invoice = inv_obj.create(inv_data)
                        # invoice = inv_obj.with_context(mail_create_nosubscribe=True).create(inv_data)
                        references[invoice] = order
                        invoices[group_key] = invoice
                    elif group_key in invoices:
                        # START HOOK
                        # This line below is added in order
                        # to cover cases where an invoice is not created
                        # and instead a draft one is picked
                        invoice = invoices[group_key]
                        # END HOOK
                        vals = {}
                        if order.name not in invoice.origin.split(", "):
                            vals["origin"] = invoice.origin + ", " + order.name
                        if (
                            order.client_order_ref
                            and order.client_order_ref
                            not in invoice.name.split(", ")
                            and order.client_order_ref != invoice.name
                        ):
                            vals["name"] = (
                                invoice.name + ", " + order.client_order_ref
                            )
                        invoice.write(vals)
                    if qty_to_invoice_date > 0 or (
                        qty_to_invoice_date < 0 and final
                    ):
                        if pending_section:
                            pending_section.invoice_line_create(
                                invoices[group_key].id,
                                pending_section.qty_to_invoice_on_date,
                            )
                            pending_section = None
                        line.invoice_line_create(
                            invoices[group_key].id, qty_to_invoice_date
                        )
                        # START HOOK
                        # Change to true if new lines are added
                        new_lines = True
                        # END HOOK
                    if references.get(invoices.get(group_key)):
                        if order not in references[invoices[group_key]]:
                            references[invoice] = references[invoice] | order

            # START HOOK
            # WAS: if not invoices:
            # Check if new lines have been added in order to determine whether
            # there are invoice lines or not
            if not new_lines and not self.env.context.get(
                "no_check_lines", False
            ):
                raise UserError(_("There is no invoicable line."))
            # END HOOK

            for invoice in invoices.values():
                #invoice.compute_taxes()    # EVITAMOS LLAMARALA DOS VECES (SE HACE MÁS ADELANTTE)
                if not invoice.invoice_line_ids:
                    raise UserError(_("There is no invoicable line."))
                # If invoice is negative, do a refund invoice instead
                if invoice.amount_untaxed < 0:
                    invoice.type = "out_refund"
                    for line in invoice.invoice_line_ids:
                        line.quantity = -line.quantity
                # Use additional field helper function (for account extensions)
                for line in invoice.invoice_line_ids:
                    line._set_additional_fields(invoice)
                # Necessary to force computation of taxes. In account_invoice,
                # they are triggered by onchanges, which are not triggered when
                # doing a create.
                invoice.compute_taxes()
                # Idem for partner
                so_payment_term_id = invoice.payment_term_id.id
                invoice._onchange_partner_id()
                # To keep the payment terms set on the SO
                invoice.payment_term_id = so_payment_term_id
                invoice.message_post_with_view(
                    "mail.message_origin_link",
                    values={"self": invoice, "origin": references[invoice]},
                    subtype_id=self.env.ref("mail.mt_note").id,
                )
            return [inv.id for inv in invoices.values()]

        self._patch_method("action_invoice_create", new_action_invoice_create)

        return res

    @api.multi
    def action_propagate_priority(self):
        for order in self:
            order.picking_ids.filtered(lambda x: x.state != "done").mapped(
                "move_lines"
            ).write({"priority": order.priority})

    @api.onchange('default_location_id')
    def _onchange_default_location_id(self):
        print ("On change defaul_location_id")
        location = self.default_location_id
        ctx = self._context.copy()
        ctx.update(location = location.id)
        for line in self.order_line:
            line.virtual_stock_conservative = line.product_id.with_context(ctx).virtual_stock_conservative


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    notes = fields.Text("Advanced Description")
    internal_notes = fields.Text("Notas internas")
    import_qty_delivered = fields.Float("Imported qty delivered", default=0)
    picking_imported = fields.Char("Imported picking")
    date_picking_imported = fields.Date("Date Imported picking")
    product_categ_id = fields.Many2one(
        related="product_id.categ_id", readonly=True
    )
    review_order = fields.Boolean(
        related="product_id.review_order", readonly=True
    )

    image_variant = fields.Binary(
        "Alternative image for line",
        attachment=True,
        help="This field holds the image used as image for the product variant, limited to 1024x1024px.",
    )
    image = fields.Binary(
        "Big-sized image",
        compute="_compute_images",
        inverse="_set_image",
        help="Image of the product variant (Big-sized image of product template if false). It is automatically "
        "resized as a 1024x1024px image, with aspect ratio preserved.",
    )
    image_small = fields.Binary(
        "Small-sized image",
        compute="_compute_images",
        inverse="_set_image_small",
        help="Image of the product variant (Small-sized image of product template if false).",
    )
    image_medium = fields.Binary(
        "Alternative image for line",
        compute="_compute_images",
        inverse="_set_image_medium",
        help="Image of the product variant (Medium-sized image of product template if false).",
    )
    package_qty = fields.Float(related="product_id.package_qty", readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 
                related= 'order_id.commercial_partner_id', 
                store=True,
                string='Commercial partner Salesperson')
    commercial_partner_user_id = fields.Many2one('res.users', 
                related= 'commercial_partner_id.user_id', 
                store=True,
                string='Commercial partner Salesperson User')
    user_id = fields.Many2one('res.users', 
                related= 'order_id.user_id', 
                store=True,
                string='Salesperson User')

    default_location_id = fields.Many2one(related= 'order_id.default_location_id')
    @api.multi
    def write(self, values):

        lines = self.env["sale.order.line"]
        if "product_id" in values and "product_uom_qty" not in values:
            lines = self.filtered(
                lambda r: r.state == "sale"
                and not r.is_expense
                and r.product_id.review_order == True
            )
        res = super(SaleOrderLine, self).write(values)
        if lines:
            orders = lines.mapped("order_id")
            for order in orders:
                if not any(order.mapped("order_line.product_id.review_order")):
                    order.pending_review = False
            lines._action_launch_stock_rule()
        return res

    @api.multi
    def _action_launch_stock_rule(self):
        rev_lines = self.filtered(lambda x: x.product_id.review_order == True)
        if rev_lines:
            self = self - rev_lines
        return super()._action_launch_stock_rule()

    ####### PARTE TEMPORAL PARA ASUMIR LA PARTE NO ENTREGADA EN LOS PEDIDOS DE
    # VENTA IMPORTADOS

    def _get_qty_procurement(self):
        qty = super()._get_qty_procurement()
        if self.import_qty_delivered and self.picking_imported:
            qty += self.import_qty_delivered
        return qty


    @api.multi
    @api.depends(
        "move_ids.state",
        "move_ids.scrapped",
        "move_ids.product_uom_qty",
        "move_ids.product_uom",
    )
    def _compute_qty_delivered(self):
        super()._compute_qty_delivered()
        for (
            line
        ) in (
            self
        ):  # TODO: maybe one day, this should be done in SQL for performance sake
            if (
                line.qty_delivered_method == "stock_move"
                or line.qty_delivered_method == "manual"
            ):
                if line.import_qty_delivered and line.picking_imported:
                    line.qty_delivered += line.import_qty_delivered

    #############################################################################

    @api.one
    @api.depends("image_variant")
    def _compute_images(self):
        if self._context.get("bin_size"):
            self.image_medium = self.image_variant
            self.image_small = self.image_variant
            self.image = self.image_variant
        else:
            resized_images = tools.image_get_resized_images(
                self.image_variant, return_big=True, avoid_resize_medium=True
            )
            self.image_medium = resized_images["image_medium"]
            self.image_small = resized_images["image_small"]
            self.image = resized_images["image"]

    @api.one
    def _set_image(self):
        self._set_image_value(self.image)

    @api.one
    def _set_image_medium(self):
        self._set_image_value(self.image_medium)

    @api.one
    def _set_image_small(self):
        self._set_image_value(self.image_small)

    @api.one
    def _set_image_value(self, value):
        if isinstance(value, pycompat.text_type):
            value = value.encode("ascii")
        image = tools.image_resize_image_big(value)

        # This is needed because when there is only one variant, the user
        # doesn't know there is a difference between template and variant, he
        # expects both images to be the same.

        self.image_variant = image

    @api.onchange("product_uom", "product_uom_qty")
    def product_uom_change(self):
        prev_price = self.price_unit
        prev_name = self.name
        res = super().product_uom_change()
        # self.product_id_change()
        if self.order_id.type_id.no_change_price and prev_price != 0:
            self.price_unit = prev_price
        if self.product_id.review_order:
            self.name = prev_name
        return res

    @api.multi
    def duplicate_line(self):
        self.ensure_one()
        self.copy({"order_id": self.order_id.id})

    def _compute_qty_to_invoice_on_date(self):
        for line in self:
            if line.invoice_policy == "product":
                invoice_policy = line.product_id.invoice_policy
            else:
                invoice_policy = line.invoice_policy

            if invoice_policy == "order":
                line.qty_to_invoice_on_date = (
                    line.product_uom_qty - line.qty_invoiced
                )
                continue
            elif self._context.get("invoice_until"):
                invoice_until = fields.Date.to_date(
                    self._context.get("invoice_until")
                )
                deliveries = line.deliveries.filtered(
                    lambda r: r.delivery_date <= invoice_until
                )
                if deliveries:
                    qty_delivered_in_date = sum(
                        [x.quantity for x in deliveries]
                    )
                    if line.picking_imported:
                        qty_delivered_in_date = qty_delivered_in_date + line.import_qty_delivered
                    line.qty_to_invoice_on_date = qty_delivered_in_date - line.qty_invoiced

                else:
                    if line.picking_imported:
                        line.qty_to_invoice_on_date = (
                            line.import_qty_delivered - line.qty_invoiced
                        )
                    else:
                        line.qty_to_invoice_on_date = -line.qty_invoiced
            else:
                line.qty_to_invoice_on_date = (
                    line.qty_delivered - line.qty_invoiced
                )

    def _search_qty_to_invoice_on_date(self, operator, operand):
        if self._context.get("invoice_until"):
            query = """
            SELECT soly.line_id
            FROM sale_order_line_delivery soly
                JOIN sale_order_line sol on soly.line_id = sol.id
            WHERE sol.invoice_status = 'to invoice'
                and sol.company_id = %(company_id)s
                and soly.delivery_date <= %(delivery_date)s
            GROUP BY soly.line_id
            HAVING SUM(soly.quantity) - SUM(sol.qty_invoiced) %(operator)s %(operand)s
            """
            params = {
                "company_id": self.env.user.company_id.id,
                "operator": operator,
                "operand": operand,
                "delivery_date": self._context.get("invoice_until"),
            }

            self.env.cr.execute(query, params)
            results = self.env.cr.fetchall()
            if results:
                return [("id", "in", [x[0] for x in results])]
        else:
            return [("qty_to_invoice", operator, operand)]

    qty_to_invoice_on_date = fields.Float(
        compute="_compute_qty_to_invoice_on_date",
        search="_search_qty_to_invoice_on_date",
    )
    qty_delivery_on_date = fields.Float(
        compute="_compute_qty_delivery_on_date",
        search="_search_qty_delivery_on_date",
    )
    deliveries = fields.One2many("sale.order.line.delivery", "line_id")


    def get_stock_moves_link_invoice(self):
        if self._context.get("invoice_until"):
            invoice_until = datetime.strptime(
                 self._context.get("invoice_until") + " 23:59:59",
                 "%Y-%m-%d %H:%M:%S",
             )
            return self.mapped('move_ids').filtered(
                lambda x: (
                    x.state == 'done' and not (any(
                        inv.state != 'cancel' for inv in x.invoice_line_ids.mapped(
                            'invoice_id'))) and not x.scrapped and (
                        x.location_dest_id.usage == 'customer' or
                        (x.location_id.usage == 'customer' and
                        x.to_refund))
                        and x.date <= invoice_until
                )
            )
        else:
            return super().get_stock_moves_link_invoice()

    # @api.multi
    # def invoice_line_create_vals(self, invoice_id, qty):
    #     res = super().invoice_line_create_vals(invoice_id, qty)
    #     if self._context.get("invoice_until"):
    #         invoice_until = datetime.strptime(
    #             self._context.get("invoice_until") + " 23:59:59",
    #             "%Y-%m-%d %H:%M:%S",
    #         )
    #         self.mapped("move_ids").filtered(
    #             lambda x: x.state == "done"
    #             and not x.invoice_line_id
    #             and not x.location_dest_id.scrap_location
    #             and x.location_dest_id.usage == "customer"
    #             and x.date <= invoice_until
    #         ).mapped("picking_id").write(
    #             {"invoice_ids": [(6, 0, [invoice_id])]}
    #         )
    #     return res

    def _compute_qty_delivery_on_date(self):
        for line in self:
            if self._context.get("delivery_until"):
                invoice_until = fields.Date.to_date(
                    self._context.get("invoice_until"))
                deliveries = line.deliveries.filtered(
                    lambda r: r.delivery_date <= invoice_until
                )
                if deliveries:
                    line.qty_delivery_on_date = sum(
                        [x.quantity for x in deliveries])
                else:
                    line.qty_delivery_on_date = 0
            else:
                line.qty_delivery_on_date = line.qty_delivered

    def _search_qty_delivery_on_date(self, operator, operand):
        if self._context.get("delivery_until"):
            query = """
            SELECT soly.line_id
            FROM sale_order_line_delivery soly
                JOIN sale_order_line sol on soly.line_id = sol.id
            WHERE sol.invoice_status = 'to invoice'
                and sol.company_id = %(company_id)s
                and soly.delivery_date <= %(delivery_date)s
            GROUP BY soly.line_id
            HAVING SUM(soly.quantity) - SUM(sol.qty_invoiced) %(operator)s %(operand)s
            """
            params = {
                "company_id": self.env.user.company_id.id,
                "operator": operator,
                "operand": operand,
                "delivery_date": self._context.get("delivery_until"),
            }

            self.env.cr.execute(query, params)
            results = self.env.cr.fetchall()
            if results:
                return [("id", "in", [x[0] for x in results])]
        else:
            return [("qty_to_invoice", operator, operand)]


    deliveries = fields.One2many("sale.order.line.delivery", "line_id")

    """   @api.multi
    def _prepare_invoice_line(self, qty):
        vals = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        if self._context.get("invoice_until") and vals.get("move_line_ids"):
            invoice_until = invoice_until = datetime.strptime(
                self._context.get("invoice_until") + " 23:59:59",
                "%Y-%m-%d %H:%M:%S",
            )
            moves = self.env["stock.move"].browse(
                vals.get("move_line_ids")[0][1]
            )
            move_line_ids = []
            for move in moves:
                if move.date <= invoice_until:
                    move_line_ids.append(move.id)
            vals["move_line_ids"] = [(4, m.id) for m in stock_moves]
        return vals """


class SaleOrderLineDelivery(models.Model):

    _name = "sale.order.line.delivery"

    line_id = fields.Many2one("sale.order.line")
    move_id = fields.Many2one('stock.move')
    quantity = fields.Float()
    delivery_date = fields.Date()