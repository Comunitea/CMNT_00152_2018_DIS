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


class AccountInvoice(models.Model):


    _inherit = 'account.invoice'

    def group_lines(self, iml, line):
        res = super(AccountInvoice,self).group_lines(iml, line)
        for move in res:
            move[2]['partner_shipping_id'] = self.partner_shipping_id.id
        return res
