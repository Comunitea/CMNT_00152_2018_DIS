# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class Settlement(models.Model):
    _inherit = 'sale.commission.settlement'

    by_goals = fields.Boolean('By Goals')

    @api.multi
    def settlement_by_goal(self):
        import ipdb; ipdb.set_trace()
        return

   
class SettlementLine(models.Model):
    _inherit = 'sale.commission.settlement.line'

    type_id = fields.Many2one('sale.order.type', 'Type')

    @api.model
    def create(self, vals):
        """
        When creating a seattlement line, if commission is by goal,
        compute it to 0
        """
        res = super().create(vals)

        if res.commission and res.commission.commission_type == 'goal':
            if res.agent_line:
                line = res.agent_line[0]
                line.settled = False  # Evito error _check_settle_integrity

                # Recalculo la comisión llamando al método compute
                # el cual termina llamando al _get_commission_amount
                # para que calcule la comision por objetico.
                line._compute_amount()

                # Aqui la línea de liquidación tiene el importe actualizado
                # debido al related del agent line, vuelvo a marcar como
                # liquidado
                type_id = res.invoice_line.sale_line_ids[0].order_id.type_id.id
                line.settled = False
                res.type_id = type_id
        return res
