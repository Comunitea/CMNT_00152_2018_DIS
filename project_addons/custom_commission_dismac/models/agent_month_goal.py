# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _


class AgentMonthGoal(models.Model):

    _name = 'agent.month.goal'

    @api.multi
    def _compute_total_goal(self):
        for amg in self:
            amg.total_goal = \
                amg.stationery_goal + amg.furniture_goal + amg.office_goal

    partner_id = fields.Many2one(
        'res.partner', 'Agent', required=True,
        domain=[('agent', '=', True)])
    month = fields.Selection([
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), 
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')], 
        string='Month', required=True)
    stationery_goal = fields.Float('Stationery Goal')
    furniture_goal = fields.Float('Furniture Goal')
    office_goal = fields.Float('Furniture Goal')
    total_goal = fields.Float('Total Goal', compute='_compute_total_goal')

    _sql_constraints = [
        ('unique_partner_month',
         'unique(partner_id, month)',
         _("You can not define same, agent and month goal")),
    ]
