# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    supplier_ref = fields.Char('Supplier reference', copy=False)


class StockMove(models.Model):

    _inherit = 'stock.move'

    def write(self, vals):
        if vals.get('quantity_done'):
            import ipdb; ipdb.set_trace()
        return super().write(vals)
