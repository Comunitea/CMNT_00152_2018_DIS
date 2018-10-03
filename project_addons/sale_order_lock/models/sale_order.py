# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    lock_allow_edit = fields.Boolean(string='Can i unlock?',
                                     compute='_compute_lock_allow_edit')
    force_unlock = fields.Boolean('Force Unlock')

    # Lock Checkboxes
    risk_lock = fields.Boolean('Locked by risk', readonly=True)
    margin_lock = fields.Boolean('Locked by margin', readonly=True)
    shipping_lock = fields.Boolean('Locked by shipping costs', readonly=True)
    locked = fields.Boolean('Locked', readonly=True)

    @api.multi
    def _compute_lock_allow_edit(self):
        """
        Check if the user can edit the lock checkbox
        """
        allow = self.env.user.\
            has_group('sale_order_lock.group_lock_manager')
        for sale in self:
            sale.lock_allow_edit = allow

    @api.multi
    def check_risk_lock(self):
        self.ensure_one()
        res = False
        if self.partner_id.avoid_locks:
            return False
        return res

    @api.multi
    def check_margin_lock(self):
        self.ensure_one()
        res = False
        if self.partner_id.avoid_locks:
            return False

        if self.team_id and self.team_id.operating_unit_id:
            min_margin = self.team_id.operating_unit_id.min_margin
            if min_margin and self.margin < min_margin:
                res = True
        return res

    @api.multi
    def check_shipping_lock(self):
        self.ensure_one()
        res = False
        if self.partner_id.avoid_locks:
            return False

        delivery_cost = 0
        for line in self.order_line.filtered('is_delivery'):
            delivery_cost += line.price_subtotal

        if delivery_cost > self.partner_id.shipping_limit:
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
            # Check if order have any lock
            risk_lock = order.check_risk_lock()
            margin_lock = order.check_margin_lock()
            shipping_lock = order.check_shipping_lock()

            locked = any([risk_lock, margin_lock, shipping_lock])

            # Writing the value of locking checks
            vals = {
                'risk_lock': risk_lock,
                'margin_lock': margin_lock,
                'shipping_lock': shipping_lock,
                'locked': locked,
            }
            ctx = self._context.copy()
            ctx.update(skip_check_locks=True)
            order.with_context(ctx).write(vals)



    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        res.check_locks()

        # Send message of lock and reason
        if res.locked:  # and not notificated
            print("TODO SEND NOTIFICATION OF LOCK, QUIZÁ EN CHECK LOCK PARA \
                QUE SE MANDE SIEMPRE??")
        return res

    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.check_locks()

        for order in self:
            # Send message of lock and reason
            if order.locked:  # and not notificated
                print("TODO SEND NOTIFICATION OF LOCK, QUIZÁ EN CHECK LOCK PARA \
                    QUE SE MANDE SIEMPRE??")
        return res

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
