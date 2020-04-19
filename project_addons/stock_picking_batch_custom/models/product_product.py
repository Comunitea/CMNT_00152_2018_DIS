# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, tools,_

from odoo.tools.float_utils import float_compare
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    qty_available_str = fields.Char('Cadena para mostrar info de stock', compute = 'compute_qty_available_str')
    putaways_str = fields.Char('Posibles ubicaciones', compute = 'compute_qty_available_str')


    @api.multi
    def compute_qty_available_str(self, location_id= False):
        if not location_id:
            picking_type_id = self._context.get('picking_type_id', False)
            if picking_type_id:
                location_id = self.env['stock.picking.type'].browse(picking_type_id).default_location_src_id
            else:
                location_id = self.env['stock.location'].browse(12)
        domain = [('fixed_location_id', 'child_of', location_id.id), ('product_id', 'in', self.ids)]
        putaways_ids = self.env['stock.fixed.putaway.strat'].search(domain)
        for product in self:
            quants = self.env['stock.quant']._gather(product_id = product, location_id = location_id)
            fisico = sum(q.quantity for q in quants)
            reservado = sum(q.reserved_quantity for q in quants)
            ubicaciones = quants.mapped('location_id.name')
            product.qty_available_str = '{} res. de {}'.format(reservado, fisico)
            putaways_str = ''
            for p in putaways_ids.filtered(lambda x:x.product_id == product):
                putaways_str = '{}-{}'.format(putaways_str, p.fixed_location_id.name)
            product.putaways_str = putaways_str[1:]