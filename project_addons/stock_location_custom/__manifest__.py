# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Location Dismac",
    "summary": "Module to import stock and customizations over stock location",
    "version": "12.0.1.0.0",
    "author": "Comunitea",
    "category": "Inventory",
    "depends": ["stock", "stock_picking_batch_extended", "stock_removal_location_by_priority"],
    "data": [
        "views/product_import_wzd_view.xml",
        "views/stock_location.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
