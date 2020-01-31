# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Cost Custom Dismac",
    "summary": "Custom costs for Dismac",
    "version": "12.0.1.0.0",
    "category": "Sales",
    "website": "comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "stock_account",
        "purchase_last_price_info",
        "customer_price",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/purchase_order.xml",
        "views/product.xml",
        "views/pricelist_item.xml",
        "views/customer_price.xml",
        "views/stock_move.xml",
        "views/stock_inventory.xml"
    ],
}
