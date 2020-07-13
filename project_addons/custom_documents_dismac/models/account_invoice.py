# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from functools import partial
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero
from collections import OrderedDict


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.model
    def _get_payments_vals(self):
        res = super()._get_payments_vals()
        sign = self.type in ["in_refund", "out_refund"] and -1 or 1
        for payment in res:
            payment['amount'] = sign * payment['amount']
        return res

    def _amount_by_group(self):
        res = super()._amount_by_group()
        for invoice in self:
            currency = invoice.currency_id or invoice.company_id.currency_id
            fmt = partial(formatLang, invoice.with_context(lang=invoice.partner_id.lang).env, currency_obj=currency)
            sign = invoice.type in ["in_refund", "out_refund"] and -1 or 1
            res = {}
            for line in invoice.tax_line_ids:
                tax = line.tax_id
                group_key = (tax.tax_group_id, tax.amount_type, tax.amount)
                res.setdefault(group_key, {'base': 0.0, 'amount': 0.0})
                res[group_key]['amount'] += line.amount_total * sign
                res[group_key]['base'] += line.base * sign
            res = sorted(res.items(), key=lambda l: l[0][0].sequence)
            invoice.amount_by_group = [(
                r[0][0].name, r[1]['amount'], r[1]['base'],
                fmt(r[1]['amount']), fmt(r[1]['base']),
                len(res),
            ) for r in res]
        return res

    def lines_grouped_by_picking(self):
        """This prepares a data structure for printing the invoice report
        grouped by pickings."""
        self.ensure_one()
        if any([x for x in self.invoice_line_ids if x.display_type]):
            return [
                {'picking': False, 'line': x, 'quantity': x.quantity}
                for x in self.invoice_line_ids
            ]
        return super().lines_grouped_by_picking()

    def split_in_pickings(self):
        self.ensure_one()
        if any([x for x in self.invoice_line_ids if x.display_type]):
            return False
        return True


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    def _compute_price_signed(self):
        for line in self:
            sign = (
                line.invoice_id.type in ["in_refund", "out_refund"] and -1 or 1
            )
            line.price_total_signed = line.price_total * sign

    price_total_signed = fields.Monetary(
        string="Amount (with Taxes)",
        compute="_compute_price_signed",
        help="Total amount with taxes",
    )
    picking_names = fields.Char(compute='_compute_picking_names')

    def _compute_picking_names(self):
        for line in self:
            line.picking_names = ', '.join(line.mapped('move_line_ids.picking_id.name'))
