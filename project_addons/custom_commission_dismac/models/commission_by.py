# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models


class CommissionBySales(models.Model):

    _name = 'commission.by.sales'

    goal_per = fields.Float('From % Goal', required=True)
    commission_id = fields.Many2one(
        'sale.commission', 'Commission', required=True)


class CommissionByMargin(models.Model):

    _name = 'commission.by.margin'

    type_id = fields.Many2one(
        comodel_name='sale.order.type', string='Type', required=True)
    coef = fields.Float('From Coeff', required=True)
    commission_id = fields.Many2one('sale.commission', 'Commission')
