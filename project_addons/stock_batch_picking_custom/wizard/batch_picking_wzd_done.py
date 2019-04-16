# -*- coding: utf-8 -*-

from odoo import api, models, fields
from pprint import pprint
from odoo.addons import decimal_precision as dp

class BatchPickingMoveDone(models.TransientModel):

    _name ="batch.picking.move.done"

    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    qty_done = fields.Float('Qty done', digits=dp.get_precision('Product Unit of Measure'))
    product_uom_qty = fields.Float('Qty ordered', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    location_id = fields.Many2one('stock.location', string="From", readonly=True)
    location_dest_id = fields.Many2one('stock.location', string="To")
    group = fields.Boolean('Is group')
    move_line_ids = fields.Many2many('stock.move')
    sale_order = fields.Many2one('sale.order')
    invisible = fields.Boolean(default=False)


    def set_as_visible(self):

        move_ids = self.mapped('move_line_ids').ids
        print (move_ids)
        batch = self._context.get('batch_id')
        batch_id = self.env['batch.picking.wzd.done'].browse(batch)
        to_show = batch_id.move_line_ids.filtered(lambda x:x.move_line_ids in move_ids)
        to_hide = batch_id.move_line_ids - to_show
        to_show.write({'invisible': False})
        to_hide.write({'invisible': True})
        print (to_show)
        print (to_hide)


class BatchPickingWzdDone(models.TransientModel):
    _name = "batch.picking.wzd.done"


    batch_id = fields.Many2one('stock.batch.picking')
    move_line_ids = fields.Many2many('batch.picking.move.done', domain=[('group', '=', False)])
    moves_done = fields.Many2many('batch.picking.move.done', domain=[('group', '=', True)])
    moves_all = fields.Many2many('batch.picking.move.done')



    def get_move_done(self, batch, moves):

        data = self.env['report.stock_batch_picking_custom.report_batch_picking_custom']._get_grouped_data(batch)
        pprint (data)
        vals=[]

        for pasillo in data:
            pprint(pasillo)
            for item in pasillo['l1_items']:
                pprint(item)
                qty = item['product_qty']
                product_uom_qty = item['product_uom_qty']
                op_ids = item['operations'].ids
                operations = [(6, 0, op_ids)]
                product_id = item['product'].id
                location_id = item['operations'][0].location_id.id
                vals.append({'qty_done': qty,
                            'move_line_ids': operations,
                            'product_id': product_id,
                            'location_id': location_id,
                            'product_uom_qty': product_uom_qty,
                            'group': True
                            })

        for move in moves:
            vals.append({'qty_done': move.qty_done,
                         'product_id': move.product_id.id,
                         'location_id': move.location_id.id,
                         'sale_order': move.sale_order.id,
                         'product_uom_qty': move.product_uom_qty,
                         'group': False,
                         'move_line_ids': [(6,0,move.id)]
                         })

        pprint (vals)
        return vals



    @api.model
    def default_get(self, fields_list):
        # We override the default_get to make stock moves created after the picking was confirmed
        # directly as available (like a force_assign). This allows to create extra move lines in
        # the fp view.
        defaults = super(BatchPickingWzdDone, self).default_get(fields_list)
        batch = self.env.context.get('active_id', False)
        if batch:
            batch_id = self.env['stock.batch.picking'].browse(batch)
            defaults['batch_id'] = batch
            vals = self.get_move_done(batch_id, batch_id.move_line_ids)
            res_g = [(0, 0, val)  for val in vals if val['group']]
            res_ng = [(0, 0, val) for val in vals if not val['group']]
            #pprint(res)
            defaults['moves_done'] = res_g
            defaults['move_line_ids'] = res_ng


        return defaults

    @api.onchange('moves_done.qty_done')
    def onchange_qty(self):
        import ipdb; ipdb.set_trace()
        for moves in self:
            continue
