# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Sale Delivered Report Dismac',
    'summary': 'Shows sale order lines current delivery status',
    'version': '0.0.0.1',
    'category': 'Custom',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'sale',
        'sale_order_type'
    ],
    'data': [
        'report/sale_delivery_report_views.xml',
        'views/product_template.xml'
    ],
}
