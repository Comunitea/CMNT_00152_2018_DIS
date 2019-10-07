# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Custom Commission Dismac',
    'version': '12.0.0.0.0',
    'category': 'Custom',
    'license': 'AGPL-3',
    'author': "Comunitea, ",
    'depends': [
        'sale_commission',
        'sales_team',
        'crm',
        'sale_order_type_operating_unit',
        'stock_account_custom'  # nuevo cálculo purchase price
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/agent_month_goal_view.xml',
        'views/res_partner_view.xml',
        'views/goal_type_view.xml',
        'views/settlement_view.xml',
        'views/account_invoice_view.xml',
        'views/sale_order_view.xml',
        'views/crm_lead_view.xml',
        'wizard/wizard_settle_view.xml',
        'wizard/change_agent_wzd_view.xml',
    ],
    'installable': True,
}
