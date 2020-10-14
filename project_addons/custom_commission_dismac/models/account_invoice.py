# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    # TODO Falta el calculo para cuando se crea factura manual?
    sale_purchase_price = fields.Float(
        string="Sale Cost", digits=dp.get_precision("Product Price"),
        readonly=True,
        copy=True
    )
    sale_purchase_price_net = fields.Float(
        string="Net Sale Cost", digits=dp.get_precision("Product Price"),
        readonly=True,
        copy=True
    )

    def check_sale_purchase_price(self):
        for line in self:
            if line.sale_line_ids and line.sale_line_ids[0].purchase_price != 0:
                line.sale_purchase_price = line.sale_line_ids[0].purchase_price
                line.sale_purchase_price_net = line.sale_line_ids[0].purchase_price_net
            elif line.product_id.type != 'product':
                # 75 % del precio venta según correo de Juan el 29/09/20
                if line.quantity != 0:
                    line.sale_purchase_price = (line.price_subtotal / line.quantity) * 0.75                    
                    line.sale_purchase_price_net = (line.price_subtotal / line.quantity) * 0.75
            elif line.product_id.last_purchase_price_fixed:
                ref_cost_price = line.product_id.reference_cost 
                cost_price = line.product_id.last_purchase_price_fixed or \
                        line.product_id.standard_price
                line.sale_purchase_price = ref_cost_price
                line.sale_purchase_price_net = cost_price


    @api.multi
    def cron_update_cost_line(self):
        lines = self.search([("sale_purchase_price", "=", 0), ('invoice_id.type', 'in', ('out_invoice', 'out_refund'))])
        print(len(lines))
        lines.check_sale_purchase_price()
        
                
    

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    coef = fields.Monetary(
        string="Margin Coef",
        compute="_get_coef",
        currency_field="currency_id",
        digits=dp.get_precision("Product Price"),
    )
    
    def action_invoice_open(self):
        for invoice in self:
            if invoice.type in ('out_invoice', 'out_refund'):
                invoice.invoice_line_ids.filtered(lambda a: a.sale_purchase_price==0).check_sale_purchase_price()
        return super().action_invoice_open()

    @api.multi
    def _get_coef(self):
        for inv in self:
            cost = sum(
                [
                    x.sale_purchase_price * x.quantity
                    for x in inv.invoice_line_ids
                ]
            )
            sale = sum(inv.invoice_line_ids.mapped("price_subtotal"))
            coef = 1
            if cost:
                coef = sale / cost
            inv.coef = coef

    @api.multi
    def get_reduced_amount(self, agent):
        """
        Busca en las líneas de agente, cual es el porcentaje de señalamiento
        y devuelve la base imponible con este porcentaje aplicado.
        Presupongo que todas las líneas del agente dado tienen el mismo
        porcentaje de reducción sobre la base imponible
        """
        res = self.amount_untaxed
        self.ensure_one()
        agent_lines = self.invoice_line_ids.mapped("agents").filtered(
            lambda a: a.agent == agent
        )
        if agent_lines:
            per = agent_lines[0].reduction_per
            res = self.amount_untaxed * (per / 100.0)
        return res
