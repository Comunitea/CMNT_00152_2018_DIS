# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock batch picking custom",
    "summary": "Customizations over stock batch picking",
    "version": "12.0.1.0.0",
    "author": "Comunitea",
    "category": "Inventory",
    "depends": ["stock_picking_batch_extended"],
    "data": [
        "views/stock_batch_picking.xml",
        "views/report_batch_picking.xml",
        "views/account_invoice.xml",
        "views/report_batch_stock_moves.xml",

        "security/ir.model.access.csv",

    ],
    "installable": True,
    "license": "AGPL-3",
}
