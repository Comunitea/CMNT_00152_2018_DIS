# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class SaleCommission(models.Model):
    _inherit = "sale.commission"

    commission_type = fields.Selection(selection_add=[('goal', 'By Goal')])
