# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale Order Lock",
    "summary": "Add min sale unit for sale orders",
    "version": "12.0.1.0.0",
    "category": "Sales",
    "website": "comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "sale",
        "account_financial_risk",
        "sale_financial_risk",
        "partner_risk_insurance",
        "sale_margin_percentage_dismac",
        "sale_order_type",
        "delivery",
    ],
    "data": [
        "security/sale_security.xml",
        "views/res_partner_view.xml",
        "views/sale_order_view.xml",
        "views/sale_order_type.xml",
        "data/ir_cron.xml",
    ],
}
