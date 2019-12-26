# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Analytic Default For Dismac",
    "summary": "Set default values for analytic in Sales and purchases",
    "version": "12.0.1.0.0",
    "category": "Accounting",
    "website": "https://www.comunitea.com/",
    "author": "Comunitea",
    "license": "AGPL-3",
    "depends": [
        "sale",
        "purchase",
        "account_analytic_default",
        "custom_analytic_account"
    ],
    "data": [
        "views/account_analytic_default_account_view.xml"
    ],
    "installable": True,
    "auto_install": False,
}
