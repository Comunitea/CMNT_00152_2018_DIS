# -*- coding: utf-8 -*-
# © 2019 Comunitea -
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    "name": "Custom Documents Dismac",
    "version": "11.0.0.0.0",
    "category": "Custom",
    "license": "AGPL-3",
    "author": "Comunitea, ",
    "depends": [
        "base",
        "sale_custom_dismac",
        "account",
        "account_due_dates_str",
        "partner_variable_decimals",
        "sale_order_report_product_image",
        "stock_picking_report_valued",
        "account_payment_partner",
        "account_invoice_report_grouped_by_picking"
    ],
    "data": [
        "views/list_reports.xml",
        "views/report_templates.xml",
        "views/stationery_report.xml",
        "views/invoice_report.xml",
        "views/order_report.xml",
        "views/internal_furniture_report.xml",
        "views/sale_proforma_invoice_report.xml",
        "views/furniture_new_report.xml",
        "views/picking_report.xml",
        "views/sale_order_type.xml",
        "data/mail_data.xml"
    ],
    "installable": True,
}
