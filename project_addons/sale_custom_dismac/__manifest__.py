# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Sale Custom Dismac',
    'summary': 'Customizations over sale flow',
    'version': '11.0.1.0.0',
    'category': 'Sales',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'sale',
        'sale_order_type',
        'sale_commission',
        'sale_margin'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'views/sale_order_type.xml'
    ],
}
