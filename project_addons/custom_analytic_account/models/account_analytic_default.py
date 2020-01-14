# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAnalyticTag(models.Model):

    _inherit = "account.analytic.tag"

    cost_center_id = fields.Many2one(comodel_name='account.cost.center',
                                        string="Cost Center")

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('analytic_tag_ids')
    def _onchange_analyic_tag_id(self):
        if self.analytic_tag_ids:
            cost_center = self.analytic_tag_ids.mapped(
                    'cost_center_id')
            if cost_center:
                self.cost_center_id = cost_center[0].id
        return

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        data = super()._prepare_invoice_line_from_po_line(line)
        if data['analytic_tag_ids']:
            aat = self.env['account.analytic.tag'].browse(data[
                                                           'analytic_tag_ids'])
            cost_center = aat.mapped(
                'cost_center_id')
            if cost_center:
                data['cost_center_id'] = cost_center[0].id
        return data

