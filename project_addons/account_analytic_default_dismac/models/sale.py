# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.onchange('product_id')
    def product_id_change(self):
        res = super().product_id_change()

        rec = self.env['account.analytic.default'].account_get(
            self.product_id.id, self.order_id.partner_id.id,
            self.order_id.user_id.id, fields.Date.today(),
            company_id=self.order_id.company_id.id)
        if rec and rec.analytic_tag_ids:
            self.analytic_tag_ids = [(6, 0, rec.analytic_tag_ids.ids)]
        return res

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self.with_context(no_account=True))._prepare_invoice_line(qty)
        rec = self.env['account.analytic.default'].account_get(
            self.product_id.id, self.order_id.partner_id.id,
            self.order_id.user_id.id, fields.Date.today())
        if not self.analytic_tag_ids:
            if rec and rec.analytic_tag_ids:
                res['analytic_tag_ids'] = [(6, 0, rec.analytic_tag_ids.ids)]
        if not self.order_id.analytic_account_id:
            if rec and rec.analytic_id.id:
                res['account_analytic_id'] = rec.analytic_id.id
        if res['analytic_tag_ids']:
            cc_ids = self.env['account.analytic.tag'].browse(res['analytic_tag_ids'][0][2]).mapped('cost_center_id')
            if cc_ids:
                res['cost_center_id'] = cc_ids[0].id

        return res
