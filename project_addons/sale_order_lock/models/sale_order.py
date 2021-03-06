# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):

    _inherit = "sale.order"

    # lock_allow_edit = fields.Boolean(string='Can i unlock?',
    #                                  compute='_compute_lock_allow_edit')
    force_unlock = fields.Boolean("Force Unlock", readonly=True, copy=False)

    # Lock Checkboxes
    risk_lock = fields.Boolean("Locked by risk", readonly=True, copy=False)
    unpaid_lock = fields.Boolean("Locked by unpaid", readonly=True, copy=False)
    margin_lock = fields.Boolean("Locked by margin", readonly=True, copy=False)
    shipping_lock = fields.Boolean(
        "Locked by shipping costs", readonly=True, copy=False
    )
    amount_lock = fields.Boolean(
        "Locked by min amount", readonly=True, copy=False
    )
    locked = fields.Boolean("Locked", readonly=True, copy=False)

    # @api.multi
    # def _compute_lock_allow_edit(self):
    #     """
    #     Check if the user can edit the lock checkbox
    #     """
    #     allow = self.env.user.\
    #         has_group('sale_order_lock.group_lock_manager')
    #     for sale in self:
    #         sale.lock_allow_edit = allow

    @api.multi
    def check_risk_lock(self):
        """
        Check if risk, but no because of any unpaid
        """
        self.ensure_one()
        res = False
        avoid_locks = self.partner_id.avoid_locks or self.commercial_partner_id.avoid_locks
        if avoid_locks:
            return False

        risk_invoice_unpaid_include = self.partner_id.risk_invoice_unpaid_include or self.partner_id.commercial_partner_id.risk_invoice_unpaid_include
        risk_invoice_unpaid = self.partner_id.risk_invoice_unpaid or self.partner_id.commercial_partner_id.risk_invoice_unpaid
        risk_invoice_unpaid_limit = self.partner_id.risk_invoice_unpaid_limit or self.partner_id.commercial_partner_id.risk_invoice_unpaid_limit
        risk_exception = self.partner_id.risk_exception or self.partner_id.commercial_partner_id.risk_exception

        if (
            not risk_invoice_unpaid_include
            or risk_invoice_unpaid
            <= risk_invoice_unpaid_limit
        ) and risk_exception:
            res = True
        return res

    @api.multi
    def check_unpaid_lock(self):
        """
        Check only if customer have unpaids
        """
        self.ensure_one()
        res = False
        avoid_locks = self.partner_id.avoid_locks or self.commercial_partner_id.avoid_locks
        if avoid_locks:
            return False
        
        risk_invoice_unpaid_include = self.partner_id.risk_invoice_unpaid_include or self.partner_id.commercial_partner_id.risk_invoice_unpaid_include
        risk_invoice_unpaid = self.partner_id.risk_invoice_unpaid or self.partner_id.commercial_partner_id.risk_invoice_unpaid
        risk_invoice_unpaid_limit = self.partner_id.risk_invoice_unpaid_limit or self.partner_id.commercial_partner_id.risk_invoice_unpaid_limit
     
        if (
            risk_invoice_unpaid_include
            and risk_invoice_unpaid
            > risk_invoice_unpaid_limit
        ):
            res = True
        return res

    @api.multi
    def check_margin_lock(self):
        self.ensure_one()
        if self.team_id.team_type == 'website':
            #Si  es una venta WEB no consideraso bloqueo
            return False
        res = False
        avoid_locks = self.partner_id.avoid_locks or self.commercial_partner_id.avoid_locks
        if avoid_locks:
            return False

        if self.type_id:
            min_margin = self.type_id.min_margin
            if min_margin and self.margin_perc < min_margin:
                res = True
        return res

    @api.multi
    def check_shipping_lock(self):
        self.ensure_one()
        res = False
        delivery_lines = self.order_line.filtered("is_delivery")
        avoid_locks = self.partner_id.avoid_locks or self.commercial_partner_id.avoid_locks
        if avoid_locks or delivery_lines:
            return False

        min_no_shipping = self.partner_id.min_no_shipping or self.partner_id.commercial_partner_id.min_no_shipping
        if (
            min_no_shipping
            and self._compute_amount_untaxed_without_delivery() < min_no_shipping
            ):
            res = True
        return res

    def _create_delivery_line(self, carrier, price_unit):
        res = super(SaleOrder, self)._create_delivery_line(carrier, price_unit)
        shipping_lock = self.check_shipping_lock()
        self.write({"shipping_lock": shipping_lock})
        return res

    def _compute_amount_untaxed_without_delivery(self):
        self.ensure_one()
        delivery_cost = sum([l.price_subtotal for l in self.order_line if l.is_delivery])
        return self.amount_untaxed - delivery_cost

    @api.multi
    def check_amount_lock(self):
        self.ensure_one()
        res = False
        avoid_locks = self.partner_id.avoid_locks or self.commercial_partner_id.avoid_locks
        if avoid_locks:
            return False

        min_amount_order = self.partner_id.min_amount_order or self.commercial_partner_id.min_amount_order
        if (
            min_amount_order
            and self._compute_amount_untaxed_without_delivery() < min_amount_order
        ):
            res = True
        return res

    @api.multi
    def check_locks(self):
        """
        Check if a sale order must be blocked, if any of the locks checks is
        setted. It also write the value for the individual lock checks
        """
        # Avoid infinity recursion because of the write method.
        if self._context.get("skip_check_locks", False):
            return

        for order in self:
            order_was_locked = order.locked
            # Check if order have any lock
            risk_lock = order.check_risk_lock()
            unpaid_lock = order.check_unpaid_lock()
            margin_lock = order.check_margin_lock()
            shipping_lock = order.check_shipping_lock()
            amount_lock = order.check_amount_lock()

            locked = any(
                [
                    risk_lock,
                    margin_lock,
                    shipping_lock,
                    unpaid_lock,
                    amount_lock,
                ]
            )

            # Writing the value of locking checks
            vals = {
                "risk_lock": risk_lock,
                "unpaid_lock": unpaid_lock,
                "margin_lock": margin_lock,
                "shipping_lock": shipping_lock,
                "amount_lock": amount_lock,
                "locked": locked,
            }
            ctx = self._context.copy()
            ctx.update(skip_check_locks=True)
            order.with_context(ctx).write(vals)

            # SEND NOTIFICATION IF ANY CHANGE IN LOCK STATUS
            pids = [order.env.user.partner_id.id]
            body = ""
            # Send message of order was locked
            if not order_was_locked and locked:
                reason_list = []
                if risk_lock:
                    reason_list.append(_("Risk"))
                if unpaid_lock:
                    reason_list.append(_("Unpaid"))
                if margin_lock:
                    reason_list.append(_("Margin"))
                if shipping_lock:
                    reason_list.append(_("No reach shipping min of %s €" % order.partner_id.min_no_shipping))
                if amount_lock:
                    reason_list.append(_("No reach min amount order of %s €" % order.partner_id.min_amount_order))

                reasons = ", ".join(reason_list)
                if not reason_list:
                    reasons = _("Unknow")
                body = _("Order %s has been locked because of: %s") % (
                    order.name,
                    reasons,
                )

            # Send message of order was unlocked
            elif order_was_locked and not locked:
                body = _("Order %s has been unlocked") % order.name

            if body:
                order.sudo().with_context(
                    mail_post_autofollow=False).message_post(
                    body=body,
                    subtype="mail.mt_note"
                )

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        res.check_locks()
        return res

    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.check_locks()
        return res

    # @api.multi
    # def copy(self, default=None):
    #     self.ensure_one()
    #     if default is None:
    #         default = {}
    #     if not default.get('name'):
    #         default.update(name=_('%s (copy)') % (self.name))
    #     return super(ResourceResource, self).copy(default)

    @api.model
    def check_unlock_sale_orders(self):
        """
        Function called by the cron
        """
        domain = [("locked", "=", True), ("state", "not in", ["done" "cancel"])]
        sale_objs = self.search(domain)
        sale_objs.check_locks()
        return True

    @api.multi
    def force_unlock_btn(self):
        self.ensure_one()
        self.write({"force_unlock": True})
        pids = [self.env.user.partner_id.id]
        user_name = self.env["res.users"].search([("id", "=", self._uid)]).name
        # Send message of order was unlocked
        body = _("Unlock forced applied by %s") % (user_name)
        self.sudo().with_context(mail_post_autofollow=False).message_post(
            body=body, subtype="mail.mt_note"
        )

    @api.multi
    def unforce_unlock_btn(self):
        self.ensure_one()
        self.write({"force_unlock": False})
        pids = [self.env.user.partner_id.id]
        user_name = self.env["res.users"].search([("id", "=", self._uid)]).name
        # Send message of order was unlocked
        body = _("No force unlock applied by %s") % user_name
        self.sudo().with_context(mail_post_autofollow=False).message_post(
            body=body, subtype="mail.mt_note"
        )

    # *********************** LOCKING FUNCTIONS *******************************
    @api.multi
    def action_draft(self):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _("This order can not be in draft becaused is locked")
                raise UserError(msg)
        res = super(SaleOrder, self).action_draft()
        return res

    @api.multi
    def action_cancel(self):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _("This order can not be cancelled becaused is locked")
                raise UserError(msg)
        res = super(SaleOrder, self).action_cancel()
        return res

    @api.multi
    def action_confirm(self):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _("This order can not be confirmed becaused is locked")
                raise UserError(msg)
        res = super(SaleOrder, self).action_confirm()
        return res

    @api.multi
    def action_done(self):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _("This order can not be finished becaused is locked")
                raise UserError(msg)
        res = super(SaleOrder, self).action_done()
        return res

    @api.multi
    def action_unlock(self):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _("This order can not be unlocked becaused is locked")
                raise UserError(msg)
        res = super(SaleOrder, self).action_unlock()
        return res

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _("This order can not be invoiced becaused is locked")
                raise UserError(msg)
        res = super(SaleOrder, self).action_invoice_create(
            grouped=grouped, final=final
        )
        return res
