# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Location Dismac",
    "summary": "Module to import stock and customizations over stock location",
    "version": "12.0.1.0.0",
    "author": "Comunitea",
    "category": "Inventory",
    "depends": ["stock", "stock_picking_batch_extended"],
    "data": [
        "views/product_import_wzd_view.xml"
    ],
    "installable": True,
    "license": "AGPL-3",
}
