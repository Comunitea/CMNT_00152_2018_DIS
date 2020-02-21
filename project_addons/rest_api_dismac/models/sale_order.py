from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    shipping_zip = fields.Char(related="partner_shipping_id.zip")
    invoice_zip = fields.Char(related="partner_invoice_id.zip")
