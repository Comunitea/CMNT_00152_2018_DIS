# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Partner custom Dismac",
    "version": "12.0.1.0.0",
    "summary": "Allows users to claim ownership over partners after a customizable time.",
    "category": "Custom",
    "author": "comunitea",
    "website": "www.comunitea.com",
    "license": "AGPL-3",
    "depends": ["sale", "sale_order_type"],
    "data": [
        "views/sale_order_view.xml",
        "views/res_partner_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
