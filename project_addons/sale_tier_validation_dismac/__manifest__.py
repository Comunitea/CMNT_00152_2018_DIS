# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Tier Validation",
    "summary": "Extends the functionality of SAle Orders to "
               "support a tier validation process.",
    "version": "11.0.1.0.0",
    "category": "Sales",
    "website": "https://github.com/OCA/purchase-workflow",
    "author": "Comunitea, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": False,
    "depends": [
        "sale",
        "base_tier_validation",
        "mail"
    ],
    "data": [
        "views/sale_order_view.xml",
        "data/mail_activity_data.xml"
    ],
}
