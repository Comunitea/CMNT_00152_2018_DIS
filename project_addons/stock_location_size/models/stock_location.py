# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class StockLocation(models.Model):

    _inherit = 'stock.location'

    def _compute_volume_free(self):
        product_uom = self.env['uom.uom']
        categ_id = self.env.ref('uom.product_uom_categ_vol').id
        ref_unit = product_uom.search(
            [('category_id', '=', categ_id), ('uom_type', '=', 'reference')])
        volume = 0.00
        for location in self.filtered('volume_unit'):
            quants_in_location = self.env['stock.quant'].search(
                [('location_id', '=', location.id)])
            for quant in quants_in_location:
                volume += quant.volume

            volume = ref_unit._compute_quantity(volume, location.volume_unit)
            location.volume_free = int(volume)

    @api.depends('length', 'width', 'height', 'volume_unit')
    def _compute_location_volume(self):
        product_uom = self.env['uom.uom']
        categ_id = self.env.ref('uom.product_uom_categ_vol').id
        ref_unit = product_uom.search(
            [('category_id', '=', categ_id), ('uom_type', '=', 'reference')])
        for loc in self.filtered('volume_unit'):
            volume = (loc.length * loc.width * loc.height) * 0.001
            loc.volume = ref_unit._compute_quantity(volume, loc.volume_unit)
            loc.volume_str = '{} {}'.format(loc.volume,  loc.volume_unit)

    size = fields.Boolean(
        "Location size",
        help="if check, this locatin has size limit\nLength x Width x Height in cm")
    length = fields.Float('Length', help="Length (cm)")
    width = fields.Float('Width', help="Width (cm)")
    height = fields.Float('Height', help="Height (cm)")
    volume_unit = fields.Many2one(
        'uom.uom', 'Volume unit',
        domain="[('category_id','ilike', 'volume')]")
    volume = fields.Float(
        'Volumen', help="Volume",
        compute="_compute_location_volume", store=True,
        digits=dp.get_precision('Stock Volume'))
    volume_str = fields.Char(
        'Volumen', compute="_compute_location_volume", store=True)
    volume_free = fields.Integer(
        'Volumen free', help="Volume", compute="_compute_volume_free")
