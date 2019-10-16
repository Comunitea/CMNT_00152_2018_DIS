# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.addons import decimal_precision as dp


class StockQuant(models.Model):

    _inherit = "stock.quant"

    def _compute_quant_volume(self):
        product_uom = self.env["uom.uom"]
        categ_id = self.env.ref("uom.product_uom_categ_vol").id
        ref_unit = product_uom.search(
            [("category_id", "=", categ_id), ("uom_type", "=", "reference")]
        )

        for quant in self:
            quant.volume = quant.product_id.volume * quant.quantity / 0.001

            quant.volumen_percent = (
                quant.volume
                * quant.location_id.volume_unit._compute_quantity(
                    quant.location_id.volume, ref_unit
                )
                * 100
            )

    volume = fields.Float(
        "Volume in l.",
        compute="_compute_quant_volume",
        help="Quant volumen in l.",
        digits=dp.get_precision("Stock Volume"),
    )
    volumen_percent = fields.Float(
        "Volume in l.",
        compute="_compute_quant_volume",
        help="% volume in location",
        digits=dp.get_precision("Stock Volume"),
    )
