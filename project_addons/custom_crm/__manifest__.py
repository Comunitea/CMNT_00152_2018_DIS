# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'CRM customizations',
    'version': '11.0.1.0.0',
    'category': 'Sales',
    'author': 'Comunitea',
    'maintainer': 'Comunitea',
    'website': 'www.comunitea.com',
    'license': 'AGPL-3',
    'depends': [
        'crm',
        'product',
        'stock_account_custom',
        'product_catalogue_ref',
    ],
    'data': [
        'views/product.xml',
        'views/res_partner.xml'
    ],
    'installable': False,
}
