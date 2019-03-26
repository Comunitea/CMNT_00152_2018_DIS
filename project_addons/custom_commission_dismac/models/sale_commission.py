# -*- coding: utf-8 -*-

from odoo import api, models, fields


class SaleCommission(models.Model):
    _inherit = "sale.commission"

    commission_type = fields.Selection(selection_add=[('goal', 'By Goal')])
