# -*- coding: utf-8 -*-
# © 2018 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    'name': 'Custom Commission Dismac',
    'version': '11.0.0.0.0',
    'category': 'Custom',
    'license': 'AGPL-3',
    'author': "Comunitea, ",
    'depends': [
        'sale_commission',
        'sales_team',
        'sale_order_type_operating_unit'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/agent_month_goal_view.xml',
        'views/res_partner_view.xml',
        'views/goal_type_view.xml',
        'views/settlement_view.xml',
    ],
    'installable': True,
}
