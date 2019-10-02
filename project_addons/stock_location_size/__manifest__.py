# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Stock Location Size and type',
    'summary': 'Add volumetrics, types ... to sstock location',
    'version': '11.0.1.0.0',
    'category': 'Product',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': False,
    'depends': [
        'stock'

    ],
    'data': [
        'data/data.xml',
        'views/stock_location.xml',
        'views/stock_quant.xml',
        'views/product_template.xml',
    ],
}
