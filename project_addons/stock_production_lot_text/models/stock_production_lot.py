# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    related_lots = fields.Text('Related Lots')
