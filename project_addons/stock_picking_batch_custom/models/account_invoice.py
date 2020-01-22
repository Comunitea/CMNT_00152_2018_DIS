# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, tools,_

from odoo.tools.float_utils import float_compare
from odoo.exceptions import ValidationError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    vendor_batch_id = fields.Many2one(
        comodel_name='stock.picking.batch',
        string='Auto-Complete'
    )

    @api.onchange('vendor_batch_id')
    def _onchange_vendor_batch_id(self):
        if not self.vendor_batch_id:
            return {}

        #self.vendor_bill_id = self.vendor_batch_id.vendor_bill_id
        purchase_ids = self.vendor_batch_id.mapped('move_lines').mapped('purchase_line_id').mapped('order_id')
        #self.purchase_id = purchase_ids and purchase_ids[0]
        if not self.vendor_batch_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.vendor_batch_id.partner_id.id

        vendor_ref = self.vendor_batch_id.name
        if vendor_ref and (not self.reference or (
                vendor_ref + ", " not in self.reference and not self.reference.endswith(vendor_ref))):
            self.reference = ", ".join([self.reference, vendor_ref]) if self.reference else vendor_ref

        currency_id = purchase_ids.mapped('currency_id')
        payment_term_id = purchase_ids.mapped('payment_term_id')

        if len(currency_id)!=1:
            raise ValidationError (_('No puedes agrupar pedidos en distintas monedas'))

        if len(payment_term_id) != 1:
            raise ValidationError(_('No puedes agrupar pedidos en distintas plazos de pago'))

        if not self.invoice_line_ids:
            # as there's no invoice line yet, we keep the currency of the PO
            self.currency_id = currency_id

        new_lines = self.env['account.invoice.line']

        for line in self.vendor_batch_id.move_lines:

            data = self._prepare_invoice_line_from_po_line(line.purchase_line_id)
            qty = line.quantity_done
            if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
                qty = 0.0
            data['quantity'] = qty
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.payment_term_id = payment_term_id
        self.env.context = dict(self.env.context, from_purchase_order_change=True)
        self.purchase_id = False
        names = purchase_ids.mapped('name')
        self.origin = ','.join(map(str, names))
        return {}