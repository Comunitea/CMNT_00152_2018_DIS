# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        return []