# © 2018 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    'name': 'Custom Pricing',
    'version': '11.0.1.0.0',
    'category': 'Custom',
    'license': 'AGPL-3',
    'author': "Comunitea",
    'depends': [
        'partner_category_discount',
        'customer_price',
        'product_pricelist_custom_dismac',
        'stock_account_custom'
    ],
    'data': [
        'views/res_partner_view.xml',
        'views/sale.xml'
    ],
}
