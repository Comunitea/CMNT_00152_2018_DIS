# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models
from odoo import tools

_logger = logging.getLogger(__name__)


class BatchGroupedMoves(models.Model):

    _name = "batch.group.move.line"

    _auto = False
    _rec_name = 'move_id'
    _order = 'src_removal_priority asc, dest_removal_priority, move_id asc, qty_no_stock asc, picking_id asc'


    @api.multi
    def _get_move_lines(self):
        for gm in self:
            domain = [('picking_id.batch_id', '=', gm.batch_id.id),
                      ('product_id', '=', gm.product_id.id),
                      ('location_id', '=', gm.location_id.id),
                      ('location_dest_id', '=', gm.location_dest_id.id)]
            sml_ids =self.env['stock.move.line'].search(domain)
            gm.move_lines = sml_ids
            gm.move_lines_count = len(sml_ids)

            gm.all_assigned = not any(x.state in ('waiting', 'confirmed', 'partially_available') for x in sml_ids.mapped('move_id') )
            gm.edit_tree = gm.move_lines_count == 1
            print ("{}".format(sml_ids.mapped('move_id').mapped('state')))
            print ("{} - {}".format(gm.id, gm.all_assigned))


    product_id = fields.Many2one('product.product', 'Articulo', readonly=True)
    move_id = fields.Many2one('stock.move', 'Movimiento', readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Albarán', readonly=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Tipo de operación', readonly=True)
    batch_id = fields.Many2one('stock.picking.batch', 'Agrupación', readonly=True)
    location_id = fields.Many2one('stock.location', 'Origen')
    location_dest_id = fields.Many2one('stock.location', 'Destino')
    src_removal_priority = fields.Integer('Prioridad O.', readonly=True)
    dest_removal_priority = fields.Integer('Prioridad D.', readonly=True)
    qty_ordered = fields.Float('C. Pedida', readonly=1)
    qty_reserved = fields.Float('C. Sin Stock', readonly=1)
    qty_no_stock = fields.Float('C. sin stock', readonly=1)
    qty_done = fields.Float('C. Hecha')
    product_uom_id = fields.Many2one(related='move_id.product_uom', string='Unidad de medida')
    move_lines = fields.One2many('stock.move.line', compute='_get_move_lines')
    n_lines = fields.Integer('Nº líneas', compute='_get_move_lines')
    edit_tree = fields.Boolean('Editable en vista', compute='_get_move_lines')
    all_assigned = fields.Boolean( compute='_get_move_lines', string="100% asignado")
    tracking = fields.Selection(related='product_id.tracking')


    def action_show_details(self):

        self.ensure_one()
        view = self.env.ref(
            "stock_picking_batch_custom.view_stock_group_move_operations"
        )
        return {
            "name": "Detalles",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "batch.group.move.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
            "context": dict(
                self.env.context,
            ),
        }


    @api.onchange('qty_done')
    def on_change(self):
        self.ensure_one()
        self.move_lines.qty_done = self.qty_done

    @api.onchange('location_id')
    def on_change(self):
        self.ensure_one()
        self.move_lines.location_id = self.location_id


    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        _select = " " \
                  "min(sml.id) as id," \
                  "min(sm.id) as move_id, " \
                  "sm.product_id as product_id, " \
                  "count(sm.picking_id) as picking_id, " \
                  "sm.picking_type_id as picking_type_id,  " \
                  "sp.batch_id as batch_id, " \
                  "spb.name as batch,  " \
                  "sum(sm.product_uom_qty) as qty_ordered," \
                  "sum(sml.product_uom_qty) as qty_reserved," \
                  "sum(not_stock) as qty_no_stock," \
                  "sum(sml.qty_done) as qty_done, sml.location_id as location_id, sml.location_dest_id as location_dest_id, " \
                  "src_removal_priority as src_removal_priority," \
                  "dest_removal_priority as dest_removal_priority "
        _from = " stock_move sm " \
              "right join stock_picking sp on sp.id = sm.picking_id " \
              "right join stock_picking_batch spb on spb.id = sp.batch_id " \
              "join stock_move_line sml on sml.move_id = sm.id " \
              "join product_product pp on pp.id = sm.product_id "
        _group = " " \
              "sm.product_id," \
              "sml.location_id, " \
              "sml.location_dest_id, " \
              "sm.picking_type_id, " \
              "sp.batch_id, " \
              "spb.name, " \
              "src_removal_priority, " \
              "dest_removal_priority " \
              "order by src_removal_priority, dest_removal_priority, sm.product_id"

        return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, _select, _from, _group)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))


class ReportPrintOpesrations(models.AbstractModel):
    _name = "report.stock_picking_batch_custom.report_batch_move_lines"

    @api.model
    def _get_report_values(self, docids, data=None):
        import pdb; pdb.set_trace()
        model = "stock.picking.batch"
        docs = self.env[model].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": model,
            "data": data,
            "docs": docs,
            "now": fields.Datetime.now,
        }