# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product import from custom xlsx",
    "summary": "Module to import custom xlsx",
    "version": "12.0.0.0.0",
    "author": "Comunitea",
    "category": "Inventory",
    "depends": [
        "stock", 
        # Por cost_ratio_id
        "stock_account_custom" 
        
            ],
    "data": [
        "wizard/product_import_custom_xlsx.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
}
