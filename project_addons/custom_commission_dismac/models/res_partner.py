# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models
from datetime import datetime


class ResPartner(models.Model):

    _inherit = 'res.partner'

    agent_goal_ids = fields.One2many(
        'agent.month.goal', 'agent_id', 'Month Objevctives', copy=False)
    agent_type = fields.Selection(selection_add=[('face', 'Presencial'),
                                  ('telemarketer', 'Teleoperadora')],
                                  default='face')

    @api.multi
    def action_view_month_goals(self):
        self.ensure_one()
        action = self.env.ref(
            'custom_commission_dismac.goals_by_month').read()[0]
        month = datetime.strptime(fields.Date.today(), '%Y-%m-%d').month
        action['context'] = {
            'default_agent_id': self.id,
            'default_month': month,
            'search_default_agent_id': self.id,
        }
        return action
