# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Sale Delivered Report Dismac',
    'summary': 'Shows sale order lines current delivery status',
    'version': '12.0.1.0.0',
    'category': 'Custom',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'sale_order_line_cancelled_qty',
        'sale_order_type',
        'purchase_open_qty',
        'web_tree_dynamic_colored_field'
    ],
    'data': [
        'report/sale_delivery_report_views.xml',
        'views/product_template.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'security/ir.model.access.csv'
    ],
}
