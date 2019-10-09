# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Product Stock Location',
    'summary': 'Add product stock location',
    'version': '12.0.1.0.0',
    'category': 'Product',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'purchase_stock'

    ],
    'data': [
        'views/product_view.xml',
    ],
}
