# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def _get_destination_location(self):
        import ipdb; ipdb.set_trace()
        res = super(PurchaseOrder, self)._get_destination_location()
        destination_location = self._context.get('destination_location', False)
        if destination_location and not self.dest_address_id and \
                destination_location in self.env['stock.location'].search_read([('id','child_of',res)]):
            return destination_location.id
        return res

class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    @api.multi
    def _prepare_stock_moves(self, picking):
        destination_location = self.product_id.property_stock_location or self.product_id.categ_id.property_stock_location or False
        if destination_location and self.order_id.picking_type_id.code == 'incoming':
            ctx = self._context.copy()
            ctx.update({'destination_location': destination_location})
            self = self.with_context(ctx)
        return  super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
