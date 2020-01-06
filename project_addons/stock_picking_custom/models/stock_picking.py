# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    number_of_packages = fields.Integer("Nº de paquetes")
    a_atencion = fields.Char('A la atención de:')