# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, models, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Paso el coste a la línea de factura, este coste viene calculado
        por el módulo dependencia stock_account_custom.
        También paso el porcentaje de señalamiento.
        """
        res = super()._prepare_invoice_line(qty)
        res.update(
            {
                "sale_purchase_price": self.purchase_price,
                "agents": [
                    (
                        0,
                        0,
                        {
                            "agent": x.agent.id,
                            "commission": x.commission.id,
                            "reduction_per": x.reduction_per,
                        },
                    )
                    for x in self.agents
                ],
            }
        )
        return res

    @api.model
    def create(self, vals):
        """
        Si al crear la línea se viene de una oportunidad con señalamiento
        Se reescriben los porcentages de reducción de la línea y se añade
        el nuevo agente con el porcentage de señalamiento adecuado.
        """
        res = super().create(vals)
        opp = res.order_id.opportunity_id
        if opp and opp.pointing:
            if not opp.user_id.partner_id.agent:
                raise UserError(
                    _(
                        "The partner related to commercial %s must be a \
                        partner"
                    )
                    % opp.user_id.name
                )
            new_agent = opp.user_id.partner_id
            pointing_per = opp.pointing_per
            res.agents.write({"reduction_per": 100.0 - pointing_per})
            res.write(
                {
                    "agents": [
                        (
                            0,
                            0,
                            {
                                "agent": new_agent.id,
                                "commission": new_agent.commission.id,
                                "reduction_per": pointing_per,
                            },
                        )
                    ]
                }
            )
        return res
