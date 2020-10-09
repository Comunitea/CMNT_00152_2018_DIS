# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock picking custom",
    "summary": "Customizations over stock picking",
    "version": "12.0.1.0.0",
    "author": "Comunitea",
    "category": "Inventory",
    "depends": ["sale_stock", "delivery", "sale_order_line_invoice_policy", "stock_picking_mass_action"],
    "data": [
        "views/stock_picking.xml",
        "views/stock_move.xml",
        "views/stock_inventory.xml",
        "report/stock_picking_delivery_tag.xml",
        #"security/ir.model.access.csv",

    ],
    "installable": True,
    "license": "AGPL-3",
}
