# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Product Stock Location',
    'summary': 'Add product stock location',
    'version': '11.0.1.0.0',
    'category': 'Product',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'stock', 'purchase'

    ],
    'data': [
        'views/product_view.xml',
    ],
}