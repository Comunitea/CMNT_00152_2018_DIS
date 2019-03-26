# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.multi
    def _compute_total_goal(self):
        for amg in self:
            amg.total_goal = \
                amg.stationery_goal + amg.furniture_goal + amg.office_goal

    agent_goal_ids = fields.One2many(
        'agent.month.goal', 'partner_id', 'Month Objevctives')
    
    total_goal = fields.Float('Total Goal', compute='_compute_total_goal')
