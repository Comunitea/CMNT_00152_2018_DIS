# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    'name': 'Product Pricelist Import Custom',
    'version': '0.0.1',
    'category': 'Custom',
    'license': 'AGPL-3',
    'author': "Comunitea, ",
    'depends': [
        'base',
        'account',
        'sale',
        'stock_available_global',
        'product_virtual_stock_conservative',
        'stock_available_global'
    ],
    'data': [
        'wizard/product_pricelist_import_wzd_view.xml',
        'security/ir.model.access.csv'
    ],
    'installable': False,
}
