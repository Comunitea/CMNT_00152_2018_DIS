# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Purchase custom Dismac',
    'summary': 'Add custom features to the Purchase model',
    'version': '11.0.1.0.0',
    'category': 'Custom',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'purchase'
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/purchase_order_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'security/ir.model.access.csv'
    ]
}