# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderType(models.Model):

    _inherit = 'sale.order.type'

    @api.multi
    def write(self, vals):
        """
        When update the operating unit, recompute sale orders
        """
        res = super(SaleOrderType, self).write(vals)
        if 'operating_unit_id' in vals:
            op_units = self.mapped('operating_unit_id')
            op_units.recompute_sale_order_locks()
        return res


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    # lock_allow_edit = fields.Boolean(string='Can i unlock?',
    #                                  compute='_compute_lock_allow_edit')
    force_unlock = fields.Boolean('Force Unlock', readonly=True)

    # Lock Checkboxes
    risk_lock = fields.Boolean('Locked by risk', readonly=True)
    unpaid_lock = fields.Boolean('Locked by unpaid', readonly=True)
    margin_lock = fields.Boolean('Locked by margin', readonly=True)
    shipping_lock = fields.Boolean('Locked by shipping costs', readonly=True)
    amount_lock = fields.Boolean('Locked by min amount', readonly=True)
    locked = fields.Boolean('Locked', readonly=True)

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
        if self.partner_id.avoid_locks:
            return False

        if (not self.partner_id.risk_invoice_unpaid_include or
                self.partner_id.risk_invoice_unpaid <=
                self.partner_id.risk_invoice_unpaid_limit) and \
                self.partner_id.risk_exception:
            res = True
        return res

    @api.multi
    def check_unpaid_lock(self):
        """
        Check only if customer have unpaids
        """
        self.ensure_one()
        res = False
        if self.partner_id.avoid_locks:
            return False

        if self.partner_id.risk_invoice_unpaid_include \
                and self.partner_id.risk_invoice_unpaid > \
                self.partner_id.risk_invoice_unpaid_limit:
            res = True
        return res

    @api.multi
    def check_margin_lock(self):
        self.ensure_one()
        res = False
        if self.partner_id.avoid_locks:
            return False

        if self.type_id and self.type_id.operating_unit_id:
            min_margin = self.type_id.operating_unit_id.min_margin
            if min_margin and self.margin < min_margin:
                res = True
        return res

    @api.multi
    def check_shipping_lock(self):
        self.ensure_one()
        res = False
        if self.partner_id.avoid_locks:
            return False

        if self.partner_id.min_no_shipping and \
                self.amount_total < self.partner_id.min_no_shipping:
            res = True
        return res

    @api.multi
    def check_amount_lock(self):
        self.ensure_one()
        res = False
        if self.partner_id.avoid_locks:
            return False

        if self.partner_id.min_amount_order and \
                self.amount_total < self.partner_id.min_amount_order:
            res = True
        return res

    @api.multi
    def check_locks(self):
        """
        Check if a sale order must be blocked, if any of the locks checks is
        setted. It also write the value for the individual lock checks
        """

        # Avoid infinity recursion because of the write method.
        if self._context.get('skip_check_locks', False):
            return

        for order in self:
            order_was_locked = order.locked
            # Check if order have any lock
            risk_lock = order.check_risk_lock()
            unpaid_lock = order.check_unpaid_lock()
            margin_lock = order.check_margin_lock()
            shipping_lock = order.check_shipping_lock()
            amount_lock = order.check_amount_lock()

            locked = any([risk_lock, margin_lock, shipping_lock, unpaid_lock,
                          amount_lock])

            # Writing the value of locking checks
            vals = {
                'risk_lock': risk_lock,
                'unpaid_lock': unpaid_lock,
                'margin_lock': margin_lock,
                'shipping_lock': shipping_lock,
                'amount_lock': amount_lock,
                'locked': locked,
            }
            ctx = self._context.copy()
            ctx.update(skip_check_locks=True)
            order.with_context(ctx).write(vals)

            # SEND NOTIFICATION IF ANY CHANGE IN LOCK STATUS
            pids = [order.env.user.partner_id.id]
            body = ''
            # Send message of order was locked
            if not order_was_locked and locked:
                reason_list = []
                if risk_lock:
                    reason_list.append(_('Risk'))
                if unpaid_lock:
                    reason_list.append(_('Unpaid'))
                if margin_lock:
                    reason_list.append(_('Margin'))
                if shipping_lock:
                    reason_list.append(_('No reach shipping min'))
                if shipping_lock:
                    reason_list.append(_('No reach min amount order'))

                reasons = ', '.join(reason_list)
                if not reason_list:
                    reasons = _('Unknow')
                body = _("Order %s has been locked because of: %s" %
                         (order.name, reasons))

            # Send message of order was unlocked
            elif order_was_locked and not locked:
                body = _("Order %s has been unlocked" % order.name)

            if body:
                order.sudo().message_post(body=body,
                                          partner_ids=[(4, pids[0])],
                                          subtype='mail.mt_note')

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

    @api.model
    def check_unlock_sale_orders(self):
        """
        Function called by the cron
        """
        domain = [
            ('locked', '=', True),
            ('state', 'not in', ['done' 'cancel'])
        ]
        sale_objs = self.search(domain)
        sale_objs.check_locks()
        return True

    @api.multi
    def force_unlock_btn(self):
        self.ensure_one()
        self.write({'force_unlock': True})

    @api.multi
    def unforce_unlock_btn(self):
        self.ensure_one()
        self.write({'force_unlock': False})

    # *********************** LOCKING FUNCTIONS *******************************
    @api.multi
    def action_draft(self):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _('This order can not be in draft becaused is locked')
                raise UserError(msg)
        res = super(SaleOrder, self).action_draft()
        return res

    @api.multi
    def action_cancel(self):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _('This order can not be cancelled becaused is locked')
                raise UserError(msg)
        res = super(SaleOrder, self).action_cancel()
        return res

    @api.multi
    def action_confirm(self):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _('This order can not be confirmed becaused is locked')
                raise UserError(msg)
        res = super(SaleOrder, self).action_confirm()
        return res

    @api.multi
    def action_done(self):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _('This order can not be finished becaused is locked')
                raise UserError(msg)
        res = super(SaleOrder, self).action_done()
        return res

    @api.multi
    def action_unlock(self):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _('This order can not be unlocked becaused is locked')
                raise UserError(msg)
        res = super(SaleOrder, self).action_unlock()
        return res

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        for order in self:
            if order.locked and order.force_unlock is False:
                msg = _('This order can not be invoiced becaused is locked')
                raise UserError(msg)
        res = super(SaleOrder, self).action_invoice_create(grouped=grouped,
                                                           final=final)
        return res
