# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address')

    @api.onchange('partner_id')
    def _onchange_delivery_address(self):
        addr = self.partner_id.address_get(['delivery'])
        self.partner_shipping_id = addr and addr.get('delivery')

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        res = super(AccountMoveLine, self)._prepare_payment_line_vals(
            payment_order)
        if not res.get('partner_bank_id') and self.partner_shipping_id or \
                (not self.partner_bank_id and not self.mandate_id):
            if len(self.partner_shipping_id.bank_ids) == 1:
                res['partner_bank_id'] = self.partner_shipping_id.bank_ids.id
        mandate = self.env['account.banking.mandate']
        if not self.mandate_id:
            partner_bank_id = res.get('partner_bank_id', False)
            if partner_bank_id:
                domain = [('partner_bank_id', '=', partner_bank_id)]
            else:
                domain = [('partner_id', '=', self.partner_shipping_id.id)]
            domain.append(('state', '=', 'valid'))
            mandate = mandate.search(domain, limit=1)
            if not mandate:
                # Si la direccion de envio no tiene mandato,
                # tal vez el partner si tenga.
                domain = [('partner_id', '=', self.partner_id.id)]
                mandate = mandate.search(domain, limit=1)
            if mandate:
                res['mandate_id'] = mandate.id
        return res

    def _prepare_analytic_line(self):
        vals = super(AccountMoveLine, self)._prepare_analytic_line()
        vals[0]['partner_shipping_id'] = self.partner_shipping_id.id
        return vals

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def group_lines(self, iml, line):
        res = super(AccountInvoice, self).group_lines(iml, line)
        for move in res:
            move[2]['partner_shipping_id'] = self.partner_shipping_id.id
        return res

    def set_mandate(self):
        res = super(AccountInvoice, self).set_mandate()
        if self.payment_mode_id.payment_method_id.mandate_required and \
                self.partner_shipping_id.valid_mandate_id:
            self.mandate_id = self.partner_shipping_id.valid_mandate_id
        return res

    @api.onchange('partner_shipping_id')
    def onchange_shipping_id(self):
        self.set_mandate()

class AccountAnalyticLine(models.Model):

    _inherit = 'account.analytic.line'

    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address')
