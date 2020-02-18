# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        return []

    date = fields.Date(default=lambda self: self._default_date())
    invoice_integration_method_ids = fields.Many2many(
        related='partner_id.invoice_integration_method_ids',
        string='Integration Method',
    )
    

    @api.model
    def _default_date(self):
        type = self.env.context.get('default_type')
        if type in ['in_invoice', 'in_refund']:
            return fields.Date.today()
