# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from .res_partner import PROCUREMENT_PRIORITIES
from odoo.tools import float_is_zero
from odoo.tools import float_compare, pycompat


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
        compute="_compute_pending_invoice_amount"
    )
    project_reference = fields.Char('Project Reference')

    def _compute_pending_invoice_amount(self):
        for order in self:
            order_amount = 0
            for line in order.order_line:
                if line.qty_to_invoice_on_date:
                    order_amount += (
                        line.qty_to_invoice_on_date * line.price_unit
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
            if any(order.mapped('order_line.product_id.review_order')):
                order.pending_review = True
                return True
            else:
                res = super().action_confirm()
                order.pending_review = False
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
                JOIN sale_order_line sol on soly.line_id = sol.id
            WHERE sol.invoice_status = 'to invoice'
                and sol.company_id = %(company_id)s
                and soly.delivery_date <= %(delivery_date)s
            GROUP BY soly.line_id, sol.order_id
            HAVING SUM(soly.quantity) - SUM(sol.qty_invoiced) > 0
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

    has_invoiceable_lines = fields.Boolean(
        compute="_compute_has_invoiceable_lines",
        search="_search_has_invoiceable_lines",
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
                    if line.display_type == "line_section":
                        pending_section = line
                        continue
                    if float_is_zero(
                        line.qty_to_invoice_on_date, precision_digits=precision
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
                    if line.qty_to_invoice_on_date > 0 or (
                        line.qty_to_invoice_on_date < 0 and final
                    ):
                        if pending_section:
                            pending_section.invoice_line_create(
                                invoices[group_key].id,
                                pending_section.qty_to_invoice_on_date,
                            )
                            pending_section = None
                        line.invoice_line_create(
                            invoices[group_key].id, line.qty_to_invoice_on_date
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
                invoice.compute_taxes()
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


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    notes = fields.Text("Advanced Description")
    internal_notes = fields.Text("Notas internas")
    import_qty_delivered = fields.Float("Imported qty delivered", default=0)
    picking_imported = fields.Char("Imported picking")
    date_picking_imported = fields.Date("Date Imported picking")

    image_variant = fields.Binary(
        "Alternative image for line", attachment=True,
        help="This field holds the image used as image for the product variant, limited to 1024x1024px.")
    image = fields.Binary(
        "Big-sized image", compute='_compute_images', inverse='_set_image',
        help="Image of the product variant (Big-sized image of product template if false). It is automatically "
             "resized as a 1024x1024px image, with aspect ratio preserved.")
    image_small = fields.Binary(
        "Small-sized image", compute='_compute_images',
        inverse='_set_image_small',
        help="Image of the product variant (Small-sized image of product template if false).")
    image_medium = fields.Binary(
        "Alternative image for line", compute='_compute_images',
        inverse='_set_image_medium',
        help="Image of the product variant (Medium-sized image of product template if false).")


####### PARTE TEMPORAL PARA ASUMIR LA PARTE NO ENTREGADA EN LOS PEDIDOS DE
    # VENTA IMPORTADOS

    def _get_qty_procurement(self):
        qty = super()._get_qty_procurement()
        if self.import_qty_delivered and self.picking_imported:
            qty += self.import_qty_delivered
        return qty

    @api.multi
    @api.depends('move_ids.state', 'move_ids.scrapped',
                 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_delivered(self):
        super()._compute_qty_delivered()
        for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
            if line.qty_delivered_method == 'stock_move':
                if line.import_qty_delivered and line.picking_imported:
                    line.qty_delivered += line.import_qty_delivered

#############################################################################

    @api.one
    @api.depends('image_variant')
    def _compute_images(self):
        if self._context.get('bin_size'):
            self.image_medium = self.image_variant
            self.image_small = self.image_variant
            self.image = self.image_variant
        else:
            resized_images = tools.image_get_resized_images(self.image_variant,
                                                            return_big=True,
                                                            avoid_resize_medium=True)
            self.image_medium = resized_images['image_medium']
            self.image_small = resized_images['image_small']
            self.image = resized_images['image']

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
            value = value.encode('ascii')
        image = tools.image_resize_image_big(value)

        # This is needed because when there is only one variant, the user
        # doesn't know there is a difference between template and variant, he
        # expects both images to be the same.

        self.image_variant = image

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        prev_price = self.price_unit
        prev_name = self.name
        res = super().product_id_change()
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
            if self._context.get("invoice_until"):
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
                    line.qty_to_invoice_on_date = (
                        qty_delivered_in_date - line.qty_invoiced
                    )
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
    deliveries = fields.One2many("sale.order.line.delivery", "line_id")


class SaleOrderLineDelivery(models.Model):

    _name = "sale.order.line.delivery"

    line_id = fields.Many2one("sale.order.line")
    quantity = fields.Float()
    delivery_date = fields.Date()
