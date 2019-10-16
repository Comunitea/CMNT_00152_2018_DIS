# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Min Sale Unit",
    "summary": "Add min sale unit for sale orders",
    "version": "12.0.1.0.0",
    "category": "Partner",
    "website": "comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["sale", "product"],
    "data": ["views/product_view.xml", "views/sale_order.xml"],
}
