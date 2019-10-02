# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Product catalogue ref',
    'summary': 'Add catalogue ref',
    'version': '11.0.1.0.0',
    'category': 'Product',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': False,
    'depends': [
        'product', 'product_multi_ean', 'sale'

    ],
    'data': [
        'views/product_view.xml',
    ],
}
