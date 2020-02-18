# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.exceptions import UserError

class ReportDelivery(models.AbstractModel):
    _name = 'report.stock.report_deliveryslip'
    _description = 'Report stock delivery'

    def compute_pending(self, docids):
        picking_id = self.env['stock.picking'].browse(docids)

        sale_id = picking_id.sale_id  # s = picking.move_lines.mapped('sale_line_id').mapped('order_id')

        domain = [('sale_line_id.order_id', '=', sale_id.id),
                  ('location_dest_id.usage', '=', 'customer'),
                  ('state', 'not in', ('draft', 'cancel', 'done'))]

        stock_moves = self.env['stock.move'].search(domain)
        vals = {}
        for move in stock_moves:
            sale_line_id = '{}'.format(move.sale_line_id.id)
            if vals.get(sale_line_id, False):
                if move.picking_id == picking_id:
                    if move.quantity_done:
                        pending = move.product_uom_qty - move.quantity_done
                    else:
                        pending = move.product_uom_qty - move.reserved_availability
                    if pending > 0:
                        vals[sale_line_id]['pending'] += pending
                else:
                    vals[sale_line_id]['pending'] += move.product_uom_qty
            else:
                if move.picking_id == picking_id:
                    if move.quantity_done:
                        pending = move.product_uom_qty - move.quantity_done
                    else:
                        pending = move.product_uom_qty - move.reserved_availability
                    if pending > 0:
                        new_line = {'name': move.sale_line_id.name,
                                    'pending': pending,
                                    'uom_name': move.product_uom.name}
                        vals[sale_line_id] = new_line
                else:
                    new_line = {'name': move.sale_line_id.name,
                                'pending': move.product_uom_qty,
                                'uom_name': move.product_uom.name}
                    vals[sale_line_id] = new_line
        res = []
        for key in vals.keys():
            res.append(vals[key])
        return res


    @api.model
    def _get_report_values(self, docids, data=None):
        picks = self.env['stock.picking'].browse(docids)
        return{
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': picks,
            'data': data,
            'pending': self.compute_pending(docids)
            }
