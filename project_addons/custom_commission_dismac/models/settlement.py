# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from datetime import datetime

class Settlement(models.Model):
    _inherit = 'sale.commission.settlement'

    by_goals = fields.Boolean('By Goals')
    unit_line_ids = fields.One2many(
        'operating.unit.settlement.line', 'settlement', 
        'Settlement by Operating Unit', readonly=True)
    

    @api.multi
    def settlement_by_goal(self):
        month_goal_obj = self.env['agent.month.goal']
        invoces_by_unit = {}

        # Agrupo Facturas porunidad operacional, (papelería, mobiliario...)
        for inv in self.lines.mapped('invoice'):
            # Líneas sin tipo de venta no comisionan
            if not inv.operating_unit_id:
                continue
            
            # Obtengo importe total y coeficiente sobre margen
            if inv.operating_unit_id not in invoces_by_unit:
                invoces_by_unit[inv.operating_unit_id] = {
                    'amont': 0.0, 'coef': 0.0}
            invoces_by_unit[inv.operating_unit_id]['amont'] += inv.amount_total
            invoces_by_unit[inv.operating_unit_id]['coef'] += 1
        
        month = datetime.strptime(self.date_to, '%Y-%m-%d').month

        # import ipdb; ipdb.set_trace()
        for op_unit in invoces_by_unit:
            # Busco objetivos para el agente en el mes dado y para la unidad
            # operacional
            domain = [
                ('month', '=', month),
                ('agent_id', '=', self.agent.id),
                ('unit_id', '=', op_unit.id)
            ]
            month_goals = month_goal_obj.search(domain)
            if not month_goals:
                continue
            goal_types = month_goals.mapped('goal_type_id')
            if not goal_types:
                continue

            # Creo una línea por cada unidad operacional liquidada
            unit_info = invoces_by_unit[op_unit]
            vals = {
                'settlement': self.id,
                'unit_id': op_unit.id
            }
            ousl = self.env['operating.unit.settlement.line'].create(vals)

            # Creo una goal.line por cada objetivo dentro de la linea de unidad
            # operacional
            goal_line_vals = []
            for gt in goal_types:
                vals = {
                    'unit_line_id': ousl.id,
                    'goal_type_id': gt.id,
                    'note': 'Explicación que apico',
                    'commission': 1.3,
                    'amount': 12145
                }
                goal_line_vals.append((0, 0, vals))
            
            ousl.write({'goal_line_ids': goal_line_vals})
        return


class OperatingUnitSettlementLine(models.Model):
    _name = 'operating.unit.settlement.line'

    settlement = fields.Many2one(
        "sale.commission.settlement", readonly=True, ondelete="cascade",
        required=True)
    unit_id = fields.Many2one(
        comodel_name='operating.unit', string='Operating Unit', required=True)
    commission = fields.Float('Commission Applied (%)')
    amount = fields.Float('Settlement Amount')
    goal_line_ids = fields.One2many(
        'goal.settlement.line', 'unit_line_id', 'Goal Lines', readonly=True)


class GoalSettlementLine(models.Model):
    _name = 'goal.settlement.line'

    unit_line_id = fields.Many2one(
        "operating.unit.settlement.line", readonly=True, ondelete="cascade",
        required=True)
    goal_type_id = fields.Many2one(
        comodel_name='goal.type', string='Type', required=False)
    note = fields.Text('Notes')
    commission = fields.Float('Commission Applied (%)')
    amount = fields.Float('Settlement Amount')
