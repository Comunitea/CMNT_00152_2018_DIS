# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Sale team product',
    'version': '0.0.0.1',
    'summary': 'Allows product customization based on sale teams',
    'category': 'Custom',
    'author': 'comunitea',
    'website': 'www.comunitea.com',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'sales_team',
        'website_sale'
    ],
    'data': [
        'views/product_template.xml'
    ],
    'installable': True,
}
