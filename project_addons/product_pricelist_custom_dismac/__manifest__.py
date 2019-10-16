# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    "name": "Product Pricelist Import Custom",
    "version": "12.0.1.0.0",
    "category": "Custom",
    "license": "AGPL-3",
    "author": "Comunitea, ",
    "depends": ["product", "product_catalogue_ref"],
    "data": [
        "wizard/product_pricelist_import_wzd_view.xml",
        "security/ir.model.access.csv",
    ],
    "external_dependencies": {"python": ["xlrd"]},
    "installable": True,
}
