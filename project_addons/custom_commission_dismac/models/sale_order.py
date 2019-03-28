# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, models


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Paso el coste a la línea de factura, este coste viene calculado
        por el módulo dependencia stock_account_custom
        """
        res = super()._prepare_invoice_line(qty)
        res.update({'sale_purchase_price': self.purchase_price})
        return res
