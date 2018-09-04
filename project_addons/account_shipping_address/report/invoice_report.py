# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address')

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ", sub.partner_shipping_id as partner_shipping_id"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() + ", ai.partner_shipping_id as partner_shipping_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", ai.partner_shipping_id"
