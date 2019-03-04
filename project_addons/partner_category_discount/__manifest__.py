# © 2019 Comunitea - Santi Argüeso <santi@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Descunetos en categorías por cliente',
    'summary': 'Establecer descuentos de venta por categoría en cadaa cliente',
    'version': '11.0.1.0.0',
    'category': 'sale',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'product',
    ],
    'data': [
        'views/category_discount.xml',
        'views/res_partner_view.xml',
        'security/ir.model.access.csv',
        'security/category_discount_security.xml'
    ],
}