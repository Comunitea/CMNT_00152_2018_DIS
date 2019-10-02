# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Sale Risk Prevention For Dismac',
    'summary': 'Customizations for risk prevention on sales',
    'version': '11.0.1.0.0',
    'category': 'Sales',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': False,
    'depends': [
        'sale',
        'sale_order_type',
        'sale_custom_dismac'
    ],
    'data': [
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'views/sale_order_type.xml'
    ],
}
