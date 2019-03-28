# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _


class GoalType(models.Model):
    _name = 'goal.type'

    name = fields.Char('Name', required=True)
    type = fields.Selection([
        ('sale_goal', 'Sale Goal'),
        ('margin_goal', 'Margin Goal'),
        ('customer_number', 'Customer Numbers'),
        ], 'Type', required=True)
    by_sale_ids = fields.One2many(
        'commission.by.sales', 'goal_type_id', 'Sale Goal Rules')
    by_margin_ids = fields.One2many(
        'commission.by.margin', 'goal_type_id', 'Margin Rules')

    @api.multi
    def get_sale_goal_commission(self, unit_info):
        commission = 0.0
        note = ''
        if not unit_info['amount_goal']:
            return 0.0
        per = round((unit_info['amount'] / unit_info['amount_goal']) * 100, 2)
        domain = [
            ('id', 'in', self.by_sale_ids.ids),
            ('goal_per', '<=', per),
        ]
        line = self.by_sale_ids.search(domain, order='goal_per desc', limit=1)
        if line:
            commission = line.commission

            note += _('Month goal: %s €\n') % unit_info['amount_goal']
            note += _('Computed amount: %s €\n') % unit_info['amount']
            note += _('Goal percentage: %s \n') % per
            note += _('Rule applied -> From percentage goal: %s') % \
                line.goal_per
        return commission, note

    @api.multi
    def get_margin_goal_commission(self, unit_info):
        commission = 0.0
        note = ''
        coef = unit_info['total_coef']
        domain = [
            ('id', 'in', self.by_margin_ids.ids),
            ('coef', '<=', coef),
        ]
        line = self.by_margin_ids.search(domain, order='coef desc', limit=1)
        if line:
            commission = line.commission
            note = _(
                'Computed coef: %s \n'
                'Rule applied -> From Margin Coeff %s'
            ) % (coef, line.coef)
        return commission, note

    @api.multi
    def get_customer_number_commission(self, unit_info):
        # TODO
        commission = 0.0
        note = 'Not implemented'
        return commission, note

    @api.multi
    def get_commission(self, unit_info):
        self.ensure_one()
        commission = 0.0
        note = ''
        if self.type == 'sale_goal':
            commission, note = self.get_sale_goal_commission(unit_info)
        elif self.type == 'margin_goal':
            commission, note = self.get_margin_goal_commission(unit_info)
        elif self.type == 'customer_number':
            commission, note = self.get_customer_number_commission(unit_info)
        return commission, note


class CommissionBySales(models.Model):

    _name = 'commission.by.sales'

    goal_type_id = fields.Many2one(
        comodel_name='goal.type', string='Goal Type', required=True)
    goal_per = fields.Float('From % Goal', required=True)
    commission = fields.Float('Commission (%)')


class CommissionByMargin(models.Model):

    _name = 'commission.by.margin'

    goal_type_id = fields.Many2one(
        comodel_name='goal.type', string='Type', required=True)
    coef = fields.Float('From Margin Coeff', required=True)
    commission = fields.Float('Commission (%)')
