# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale Custom Dismac",
    "summary": "Customizations over sale flow",
    "version": "12.0.1.0.0",
    "category": "Sales",
    "website": "comunitea.com",
    "author": "Comunitea",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale",
        "sale_order_type",
        "sale_commission",
        "sale_margin_percentage_dismac",
        "sale_order_revision",
        "sale_order_line_form_button",
        "sale_order_action_invoice_create_hook",
        "stock_picking_complete_info",
        "l10n_es_facturae",
        'sale_order_line_invoice_policy',
        'stock_picking_invoice_link',
        'stock_picking_report_valued'
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/apply_global_discount.xml",
        "wizard/sale_invoice_on_date.xml",
        "wizard/sale_line_change_product.xml",
        "views/res_partner_view.xml",
        "views/sale_order_view.xml",
        "views/sale_order_type.xml",
        "views/report_sale_order.xml",
        "views/product_view.xml",
        "views/stock_picking.xml",
        "views/sale_report_view.xml",
        "views/invoice_integration_view.xml"
    ],
}
