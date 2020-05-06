# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

class StockLocation(models.Model):
    _inherit = 'stock.location'

    def name_get(self):
        if self._context.get('show_product_id_qty', False):
            ret_list = []
            product_id = self.env['product.product'].browse(self._context['show_product_id_qty'])
            for location in self:
                quants = self.env['stock.quant']._gather(product_id, location)
                qty_available = sum((x.quantity - x.reserved_quantity) for x in quants)
                orig_location = location
                name = location.name
                while location.location_id and location.usage != 'view':
                    location = location.location_id
                    name = location.name + "/" + name
                name = '{}: {} {}'.format(name, qty_available, product_id.uom_id.name)
                ret_list.append((orig_location.id, name))
            return ret_list
        return super().name_get()
