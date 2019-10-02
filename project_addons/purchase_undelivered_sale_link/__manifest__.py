# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Purchase to Undelivered Sale Link',
    'summary': 'Shows sale order lines undelivered and link with purchase order',
    'version': '0.0.0.1',
    'category': 'Custom',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': False,
    'depends': [
        'stock', 'purchase'
    ],
    'data': [
        'report/purchase_to_undelivered_link_report.xml',
        'views/purchase_views.xml',
        'security/ir.model.access.csv'
    ],
}
