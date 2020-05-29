# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models
from odoo import tools

_logger = logging.getLogger(__name__)

class BatchGroupedMovesWzd(models.TransientModel):
    _name = "batch.group.move.line.wzd"
    
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
    qty_reserved = fields.Float('C. Reservada', readonly=1)
    qty_no_stock = fields.Float('C. sin stock', readonly=1)
    qty_done = fields.Float('C. Hecha')
    product_uom_id = fields.Many2one(related='move_id.product_uom', string='Unidad de medida')
    move_lines = fields.Many2many('stock.move.line', string='Operaciones')
    n_lines = fields.Integer('Nº líneas')
    edit_tree = fields.Boolean('Editable en vista')
    all_assigned = fields.Boolean( string="100% asignado")
    tracking = fields.Selection(related='product_id.tracking')
    grouped_id = fields.Many2one('batch.group.move.line')
    picking_ids = fields.Many2many('stock.picking')
    sale_line_ids = fields.Many2many('sale.order.line')
    move_ids = fields.Many2many('stock.move')


class BatchGroupedMoves(models.Model):
    _name = "batch.group.move.line"
    _auto = False
    _rec_name = 'move_id'
    _order = 'src_removal_priority asc, dest_removal_priority, move_id asc, qty_no_stock asc, picking_id asc'

    @api.multi
    def _get_move_lines(self):
        if not self:
            return
        for gm in self:
            domain = [('picking_id.batch_id', '=', gm.batch_id.id),
                      ('product_id', '=', gm.product_id.id)]

            if gm.picking_type_id.code == 'outgoing':
                domain += [('location_dest_id', '=', gm.location_dest_id.id)]
            elif gm.picking_type_id.code == 'incoming':
                domain += [('location_id', '=', gm.location_id.id)]
            else:
                domain +=[('location_dest_id', '=', gm.location_dest_id.id), ('location_id', '=', gm.location_id.id)]

            sml_ids =self.env['stock.move.line'].search(domain)
            product_moves = gm.picking_ids.mapped('move_lines').filtered(lambda x:x.product_id== gm.product_id)
            my_moves = sml_ids.filtered(lambda x: x.location_id == gm.location_id and x.location_dest_id == gm.location_dest_id)
            gm.move_lines = sml_ids
            gm.n_lines = len(sml_ids)
            gm.all_assigned = not any(x.state in ('waiting', 'confirmed', 'partially_available') for x in sml_ids.mapped('move_id') )
            gm.edit_tree = gm.n_lines == 1
            gm.show_apply_qties = gm.qty_done != (gm.qty_reserved + gm.qty_no_stock)
            gm.move_ids = product_moves
            #gm.picking_ids = gm.batch_id.picking_ids
            gm.sale_line_ids = product_moves.mapped('sale_line_id')
            gm.product_qty_ordered = sum(x.product_uom_qty for x in product_moves)
            gm.product_qty_reserved = sum(x.reserved_availability for x in product_moves)
            product_qty_done = sum(x.quantity_done for x in product_moves)
            if product_qty_done == gm.product_qty_ordered:
                gm.qty_reserved_str = '{} de {}'.format(gm.qty_done or gm.qty_reserved, gm.product_qty_ordered)
            else:
                gm.qty_reserved_str = 'Faltan {} de {}'.format(gm.product_qty_ordered - product_qty_done, gm.product_qty_ordered)

    product_id = fields.Many2one('product.product', 'Articulo', readonly=True)
    move_id = fields.Many2one('stock.move', 'Movimiento', readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Albarán', readonly=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Tipo de operación', readonly=True)
    batch_id = fields.Many2one('stock.picking.batch', 'Agrupación', readonly=True)
    location_id = fields.Many2one('stock.location', 'Origen')
    location_dest_id = fields.Many2one('stock.location', 'Destino')
    move_location_id = fields.Many2one('stock.location', 'Origen')
    move_location_dest_id = fields.Many2one('stock.location', 'Destino')
    src_removal_priority = fields.Integer('Prioridad O.', readonly=True)
    dest_removal_priority = fields.Integer('Prioridad D.', readonly=True)
    qty_ordered = fields.Float('C. Pedida x Est', readonly=1)#, compute='_get_move_lines')
    qty_reserved = fields.Float('C. Reservada x Est', readonly=1)# , compute='_get_move_lines')
    qty_no_stock = fields.Float('C. sin stock', readonly=1)
    qty_done = fields.Float('C. Hecha x Est.', readonly=1)
    product_qty_ordered = fields.Float('C. Pedida Total', compute='_get_move_lines')
    product_qty_reserved = fields.Float('C. Reservada Total', compute='_get_move_lines')
    qty_reserved_str = fields.Char('Estado', compute='_get_move_lines')
    product_uom_id = fields.Many2one(related='move_id.product_uom', string='Unidad de medida')
    move_lines = fields.One2many('stock.move.line', compute='_get_move_lines')
    n_lines = fields.Integer('Nº líneas', compute='_get_move_lines')
    edit_tree = fields.Boolean('Editable en vista', compute='_get_move_lines')
    all_assigned = fields.Boolean(compute='_get_move_lines', string="100% asignado")
    tracking = fields.Selection(related='product_id.tracking')
    show_apply_qties = fields.Boolean(compute="_get_move_lines")
    picking_ids = fields.One2many(related='batch_id.picking_ids')
    move_ids = fields.One2many('stock.move', compute='_get_move_lines')
    sale_line_ids = fields.One2many('sale.order.line', compute='_get_move_lines')
    product_location_ids = fields.One2many('stock.location', compute="_compute_product_location")
    domain_location_ids = fields.One2many('stock.location', compute="_compute_product_location")
    product_qty_by_location = fields.Float('C. en la ubicación', compute="_compute_product_location")
    ref = fields.Char('Cant', compute="_get_move_lines")


    def _compute_state(self, move_lines):
        '''compiat de state de stock_picking, pero para group en vez de move_lines'''
        ''' State of a picking depends on the state of its related stock.move
        - Draft: only used for "planned pickings"
        - Waiting: if the picking is not ready to be sent so if
          - (a) no quantity could be reserved at all or if
          - (b) some quantities could be reserved and the shipping policy is "deliver all at once"
        - Waiting another move: if the picking is waiting for another move
        - Ready: if the picking is ready to be sent so if:
          - (a) all quantities are reserved or if
          - (b) some quantities could be reserved and the shipping policy is "as soon as possible"
        - Done: if the picking is done.
        - Cancelled: if the picking is cancelled
        '''

        if not move_lines:
            state = 'draft'
        elif any(move.state == 'draft' for move in move_lines):  # TDE FIXME: should be all ?
                state = 'draft'
        elif all(move.state == 'cancel' for move in move_lines):
            self.state = 'cancel'
        elif all(move.state in ['cancel', 'done'] for move in move_lines):
            self.state = 'done'
        else:
            relevant_move_state = move_lines._get_relevant_state_among_moves()
            if relevant_move_state == 'partially_available':
                state = 'assigned'
            else:
                state = relevant_move_state
        return state

    @api.multi
    def _compute_product_location(self):
        for line in self:
            quants =  self.env['stock.quant']._gather(line.product_id, line.move_location_id)
            line.product_location_ids = quants.mapped('location_id')
            line.product_qty_by_location = sum((x.quantity - x.reserved_quantity) for x in quants)
            line.domain_location_ids = line.product_location_ids

    @api.multi
    def write(self, vals):
        if 'move_lines' in vals:
            for update in vals['move_lines']:
                if update[0] == 1:
                    self.env['stock.move.line'].browse(update[1]).write(update[2])
            vals.pop('move_lines')
        if not vals:
            return True
        return super().write(vals=vals)

    @api.multi
    def apply_change(self):
        for line in self.move_lines:
            line_id = self.env['stock.move.line'].browse(line.id)
            vals = {'location_dest_id': line.location_dest_id.id, 'location_id': line.location_id.id, 'qty_done': line.qty_done}
            line_id.write(vals)
        return True

    @api.multi
    def action_apply_qties(self):
        sml_ids = self.mapped('move_lines')
        sml_ids.apply_reserved_to_done_qties()
        return True

    def creategroup_wzd(self):

        vals = {'product_id': self.product_id.id,
                'grouped_id': self.id,
                'move_id': self.move_id.id,
                'picking_type_id': self.picking_type_id.id,
                'batch_id': self.batch_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'qty_ordered': self.qty_ordered,
                'qty_reserved': self.qty_reserved,
                'qty_no_stock': self.qty_no_stock,
                'qty_done': self.qty_done,
                'product_uom_id': self.product_uom_id.id,
                'sale_line_ids': [(6, 0, self.move_lines.mapped('sale_line_id').ids)],
                'picking_ids': [(6, 0, self.move_lines.mapped('picking_id').ids)],
                'move_lines': [(6,0, self.move_lines.ids)],
                'move_ids': [(6, 0, self.move_ids.ids)],
                'n_selfs': self.n_lines,
                'edit_tree': self.edit_tree,
                'tracking': self.tracking,
                'all_assigned': self.all_assigned}
        return self.env['batch.group.move.line.wzd'].create(vals)
        
    def action_show_details(self):
        view = self.env.ref(
            "stock_picking_batch_custom.view_stock_group_move_operations_no_wzd"
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

        new_wzd = self.creategroup_wzd()
        new_wzd.ensure_one()
        view = self.env.ref(
            "stock_picking_batch_custom.view_stock_group_move_operations"
        )
        return {
            "name": "Detalles",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "batch.group.move.line.wzd",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "self",
            "res_id": new_wzd.id,
            "context": dict(
                new_wzd.env.context,
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
                  "row_number() over () as id," \
                  "min(sm.id) as move_id, " \
                  "sm.product_id as product_id, " \
                  "count(sm.picking_id) as picking_id, " \
                  "sm.picking_type_id as picking_type_id,  " \
                  "sp.batch_id as batch_id, " \
                  "spb.name as batch,  " \
                  "sum(not_stock + sml.product_uom_qty) as qty_ordered," \
                  "sum(sml.product_uom_qty) as qty_reserved," \
                  "sum(not_stock) as qty_no_stock," \
                  "sum(sml.qty_done) as qty_done, " \
                  "coalesce(sml.location_id, sm.location_id) as location_id, " \
                  "coalesce(sml.location_dest_id, sm.location_dest_id) as location_dest_id, " \
                  "sm.location_id as move_location_id, " \
                  "sm.location_dest_id as move_location_dest_id, " \
                  "coalesce(src_removal_priority, 0) as src_removal_priority," \
                  "coalesce(dest_removal_priority, 0) as dest_removal_priority " \

        _from = " stock_move sm " \
              "right join stock_picking sp on sp.id = sm.picking_id " \
              "right join stock_picking_batch spb on spb.id = sp.batch_id " \
              "left join stock_move_line sml on sml.move_id = sm.id " \
              "join product_product pp on pp.id = sm.product_id "
        _group = " " \
              "sm.product_id," \
              "sm.location_id, " \
              "sml.location_id, " \
              "sml.location_dest_id, " \
              "sm.location_dest_id, " \
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
        sql = """CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query())
        print (sql)
        self.env.cr.execute(sql)


class ReportPrintOpesrations(models.AbstractModel):
    _name = "report.stock_picking_batch_custom.report_batch_move_lines"

    @api.model
    def _get_report_values(self, docids, data=None):
        model = "stock.picking.batch"
        docs = self.env[model].browse(docids)
        docs.write({'state': 'in_progress'})
        return {
            "doc_ids": docids,
            "doc_model": model,
            "data": data,
            "docs": docs,
            "now": fields.Datetime.now,
        }