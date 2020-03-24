# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def get_transaction_data(self):

        for line in self.invoice_line_ids:
            sales = line.sale_line_ids.mapped('order_id')
            if sales:
                sale_name = sales[0].name
                sale_date = sales[0].confirmation_date.date()
                sale_reference = sales[0].client_order_ref or False
                line.write({
                    'facturae_issuer_transaction_reference': sale_name,
                    'facturae_issuer_transaction_date': sale_date,
                    'facturae_receiver_transaction_reference': sale_reference,
                })

    @api.multi
    def action_integrations(self):
        self.ensure_one()
        self.get_transaction_data()
        return super().action_integrations()
 