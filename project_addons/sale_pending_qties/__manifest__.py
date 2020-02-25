# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale Pending Qties",
    "version": "12.0.1.0.0",
    "summary": "Muestra las cantidades pendientes en albaranes para un pedido",
    "category": "Sale",
    "author": "comunitea",
    "website": "www.comunitea.com",
    "license": "AGPL-3",
    "depends": ["sale_stock", "custom_documents_dismac"],
    "data": [
        "views/sale.xml",
        "report/report_delivery.xml"
    ],
    "installable": True,
}
