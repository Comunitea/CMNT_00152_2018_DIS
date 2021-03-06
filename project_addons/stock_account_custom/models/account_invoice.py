# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# Copyright 2019 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        res = super().action_invoice_open()
        for rec in self:
            if rec.type in ['in_invoice', 'in_refund']:
                rec.invoice_line_ids.mapped('product_id').set_product_last_purchase(
                    rec.id)
                rec.invoice_line_ids.mapped('product_id')._set_last_purchase_fixed()
        return res

    @api.multi
    def action_invoice_cancel(self):
        res = super().action_invoice_cancel()
        for rec in self:
             if rec.type in ['in_invoice', 'in_refund']:
                rec.invoice_line_ids.mapped('product_id').set_product_last_purchase(
                    rec.id)
                rec.invoice_line_ids.mapped('product_id')._set_last_purchase_fixed()
        return res
