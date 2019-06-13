# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, models, fields


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Paso el coste a la línea de factura, este coste viene calculado
        por el módulo dependencia stock_account_custom.
        También paso el porcentaje de señalamiento.
        """
        res = super()._prepare_invoice_line(qty)
        res.update({
            'sale_purchase_price': self.purchase_price,
            'agents': [(0, 0, {
                'agent': x.agent.id,
                'commission': x.commission.id,
                'reduction_amount': x.reduction_amount}) for x in self.agents]
        })
        return res


class SaleOrderLineAgent(models.AbstractModel):
    _inherit = "sale.commission.line.mixin"

    reduction_per = fields.Float(
        '% Over subtotal', default=100.0, 
        help='Compute settlement with % reduced over invoices subtotal')
