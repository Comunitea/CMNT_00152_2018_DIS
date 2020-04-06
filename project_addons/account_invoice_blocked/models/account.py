# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.osv import expression


class AccountJournal(models.Model):

    _inherit = "account.journal"

    block_payments = fields.Boolean(
        "Block Payments"
    )


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super().finalize_invoice_move_lines(move_lines)
        if self.journal_id.block_payments:
            for move in move_lines:
                move[2]['blocked']=True
        return move_lines
