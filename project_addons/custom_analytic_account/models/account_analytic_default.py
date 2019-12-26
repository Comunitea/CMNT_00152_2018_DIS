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

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super()._onchange_product_id()
        if self.analytic_tag_ids:
            self.cost_center_id = self.cost_center_id = \
                self.analytic_tag_ids.mapped(
                'cost_center_id')[0].id
        return res
