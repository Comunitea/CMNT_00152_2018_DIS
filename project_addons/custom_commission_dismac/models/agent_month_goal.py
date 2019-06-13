# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _


class AgentMonthGoal(models.Model):

    _name = 'agent.month.goal'

    agent_id = fields.Many2one(
        'res.partner', 'Agent', required=True,
        domain=[('agent', '=', True)])
    month = fields.Selection([
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), 
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')], 
        string='Month', required=True)
    unit_id = fields.Many2one('operating.unit', 'Operating Unit')
    amount_goal = fields.Float('Amount Goal')
    min_customers = fields.Integer('Min customers')
    goal_type_id = fields.Many2one('goal.type', 'Goal Type')

    _sql_constraints = [
        ('unique_partner_month',
         'unique(agent_id, month, unit_id, goal_type_id)',
         _("You can not define same, agent, month, operating unit, \
            and goal type")),
    ]
