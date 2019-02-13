# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Sale Order Line Add stock fields',
    'summary': 'Add stock fields to sale orders',
    'version': '11.0.1.0.0',
    'category': 'Sales',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'installable': True,
    'depends': [
        'sale',
    ],
    'data': [
        'views/sale_order_view.xml'
    ],
}