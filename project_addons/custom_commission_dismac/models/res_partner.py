# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class ResPartner(models.Model):

    _inherit = 'res.partner'

    agent_goal_ids = fields.One2many(
        'agent.month.goal', 'partner_id', 'Month Objevctives')
    #TODO campo coeff
