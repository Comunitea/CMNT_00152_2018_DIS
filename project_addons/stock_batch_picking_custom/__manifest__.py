# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Stock batch picking custom',
    'summary': 'Customizations over stock batch picking',
    'version': '11.0.1.0.0',
    'author': "Comunitea" ,
    'category': 'Inventory',
    'depends': [
        'stock_batch_picking',
    ],
    'data': [

        'views/stock_batch_picking.xml',
        #'views/product_product.xml',
        'views/report_batch_picking.xml',
        #'views/stock_picking.xml',
        #'views/stock_warehouse.xml',
        #'wizard/batch_picking_wzd_done.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
