# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class SaleInvoiceOnDate(models.TransientModel):

    _name = 'sale.invoice.on.date'

    invoice_until_date = fields.Date()

    def view_invoiceable_orders(self):
        action = self.env.ref('sale.action_orders').read()[0]
        action['context'] = {
            'search_default_invoiceable_sales': True,
            'search_default_invoice_until': self.invoice_until_date}
        return action
