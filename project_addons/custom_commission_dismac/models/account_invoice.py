# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    sale_purchase_price = fields.Float(
        string='Sale Cost', digits=dp.get_precision('Product Price'))


class AccountInvoicer(models.Model):
    _inherit = "account.invoice"

    coef = fields.Monetary(
        string="Margin Coef",
        compute='_get_coef', currency_field='currency_id',
        digits=dp.get_precision('Product Price'))

    @api.multi
    def _get_coef(self):
        for inv in self:
            cost = \
                sum([x.sale_purchase_price * x.quantity
                     for x in inv.invoice_line_ids])
            sale = sum(inv.invoice_line_ids.mapped('price_subtotal'))
            coef = 1
            if cost:
                coef = sale / cost
            inv.coef = coef