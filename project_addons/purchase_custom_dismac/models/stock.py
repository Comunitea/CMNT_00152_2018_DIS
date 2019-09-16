# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from datetime import datetime

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    supplier_ref = fields.Char('Supplier reference', copy=False)