# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Sale order line history',
    'version': '11.0.1.0.0',
    'summary': 'Show line history in sale order',
    'category': 'Sale',
    'author': 'comunitea',
    'website': 'www.comunitea.com',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'onchange_helper',
    ],
    'data': [
        'wizard/sale_line_history_add_to_order.xml',
        'views/sale.xml',
        'views/res_partner.xml'
    ],
    'installable': True,
}
