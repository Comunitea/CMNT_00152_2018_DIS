# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models

class GoalType(models.Model):
    _name = 'goal.type'

    name = fields.Char('Name', required=True)
    type = fields.Selection([
        ('sale_goal', 'Sale Goal'),
        ('margin_goal', 'Margin Goal'),
        ('customer_number', 'Customer Number'),
        ], 'Type', required=True)
    by_sale_ids = fields.One2many(
        'commission.by.sales', 'goal_type_id', 'Sale Goal Rules')
    by_margin_ids = fields.One2many(
        'commission.by.margin', 'goal_type_id', 'Margin Rules')


class CommissionBySales(models.Model):

    _name = 'commission.by.sales'

    goal_type_id = fields.Many2one(
        comodel_name='goal.type', string='Type', required=True)
    goal_per = fields.Float('From % Goal', required=True)
    commission = fields.Float('Commission (%)')
    


class CommissionByMargin(models.Model):

    _name = 'commission.by.margin'

    goal_type_id = fields.Many2one(
        comodel_name='goal.type', string='Type', required=True)
    coef = fields.Float('From Coeff', required=True)
    commission = fields.Float('Commission (%)')
