# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Text in production lot',
    'summary': 'Add Text field to production lot',
    'version': '11.0.1.0.0',
    'category': 'Stock',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'stock'

    ],
    'data': [
        'views/stock_production_lot_view.xml',
    ],
}
