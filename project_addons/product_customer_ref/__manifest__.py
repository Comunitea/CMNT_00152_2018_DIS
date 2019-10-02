# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Product customer ref',
    'summary': 'Add customer ref',
    'version': '11.0.1.0.0',
    'category': 'Product',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': False,
    'depends': [
        'product',
        'sale',
        'sale_team_product_custom_dismac'

    ],
    'data': [
        'views/product_view.xml',
        'views/product_customer_value.xml',
        'views/res_partner.xml',
        'security/ir.model.access.csv'
    ],
}
