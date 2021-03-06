# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models

from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare

class BatchPickingGroupMove(models.Model):

    _name = "batch.picking.group.move"

    group_product_id = fields.Many2one(
        "product.product", string="Product", store=False
    )
    product_id = fields.Many2one(
        "product.product", string="Product", readonly=True
    )
    qty_done = fields.Float(digits=dp.get_precision("Product Unit of Measure"), compute="get_qty_done", inverse="set_qty_done")
    product_uom_qty = fields.Float(
        "Qty ordered",
        digits=dp.get_precision("Product Unit of Measure"),
        readonly=True,
    )
    location_id = fields.Many2one(
        "stock.location", string="From", readonly=True
    )
    location_dest_id = fields.Many2one("stock.location", string="To")
    group = fields.Boolean("Is group")
    move_line_ids = fields.Many2many("stock.move.line")
    sale_order = fields.Many2one("sale.order")
    invisible = fields.Boolean(default=False)
    batch_id = fields.Many2one("stock.picking.batch")
    product_uom = fields.Many2one(related="product_id.uom_id")
    n_moves = fields.Integer("N lineas", compute="get_qty_done")
    tracking = fields.Char()

    def set_qty_done(self):
        self.ensure_one()
        if not self.move_line_ids or not len(self.move_line_ids) == 1:
            raise ValidationError('No puedes cambiar aquí si tienes más de un pedido/ubicación de origen: {}'.format(self.n_moves))
        if self.product_id.tracking != 'none':
            raise ValidationError('No puedes cambiar aquí la cantidad ya que el artículo {} tiene trazabilidad'.format(self.product_id.display_name))
        self.move_line_ids.qty_done = self.qty_done


    @api.multi
    def get_qty_done(self):
        for move in self:
            move.qty_done = sum(x.qty_done for x in move.move_line_ids)
            move.n_moves = len(move.move_line_ids)

    @api.multi
    def action_apply_qties(self):

        if self._context.get('fill_qty_done', False):
            for line in self:
                for sm_id in line.move_line_ids.filtered(lambda x: x.not_stock == 0):
                    sm_id.qty_done = sm_id.product_uom_qty
                line.qty_done = sum(x.qty_done for x in line.move_line_ids)
        else:
            for line in self:
                if line.qty_done == sum(x.product_uom_qty for x in line.move_line_ids):
                    for move_line in line.move_line_ids:
                        move_line.qty_done = move_line.product_uom_qty
                else:
                    moves_sorted = line.move_line_ids.sorted(
                        lambda x: x.sale_order.date_order
                    )
                    qty_available = line.qty_done
                    for move_line in moves_sorted:
                        if qty_available >= move_line.product_uom_qty:
                            move_line.qty_done = move_line.product_uom_qty
                        else:
                            move_line.qty_done = qty_available
                        qty_available -= move_line.qty_done

                        if qty_available < 0.00:
                            break



    def action_show_details(self):

        self.ensure_one()
        view = self.env.ref(
            "stock_picking_batch_custom.view_stock_group_move_operations"
        )
        move = self.move_line_ids and self.move_line_ids[0]
        if move:
            move_id = move.move_id
        return {
            "name": _("Detailed Operations"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "batch.picking.group.move",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
            "context": dict(
                self.env.context),
        }


class StockBatchPicking(models.Model):

    _inherit = "stock.picking.batch"

    @api.multi
    def get_moves_count(self):
        for batch in self:
            batch.moves_all_count = len(batch.move_lines)

    auto_fill_done = fields.Boolean('Cantidad hecha auto', default=True, help ="Si está marcado, pone las cantidades hechas al reservar")
    moves_all_count = fields.Integer("Moves count", compute=get_moves_count)
    qty_applied = fields.Boolean(default=False)
    grouped_move_line = fields.One2many('batch.group.move.line', 'batch_id', string="Lineas agrupadas de picking")

    def action_view_stock_picking_related(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read([])[0]
        action['domain'] = [('id', 'in', self.picking_dest_ids.ids)]
        return action

    def action_view_grouped_line(self):
        self.ensure_one()
        action = self.env.ref('stock_picking_batch_custom.action_stock_group_move_tree_operations').read([])[0]
        action['domain'] = [('batch_id', '=', self.id)]
        action['target'] = 'current'
        return action

    def action_show_moves_kanban(self):
        self.ensure_one()
        view = self.env.ref(
            "stock.view_stock_move_line_kanban"
        )
        return {
            "name": _("Detailed Operations"),
            "type": "ir.actions.act_window",
            "view_type": "kanban",
            "view_mode": "form",
            "res_model": "stock.move.line",
            "views": [(view.id, "kanban")],
            "view_id": view.id,
            "context": dict(self.env.context),
            "domain": [('id', 'in', self.move_line_ids.ids)]
        }

    @api.constrains("picking_ids")
    def _check_type(self):
        if len(self.picking_ids.mapped("picking_type_id")) > 1:
            raise ValidationError(_("All pickings in batch must be same type"))

    @api.multi
    def action_group(self):
        self.write({'state':'in_progress'})

    @api.multi
    def action_cancel_group(self):
        self.move_lines.mapped('move_line_ids').filtered(lambda x:not x.qty_done and x.not_stock >0).unlink()

    @api.multi
    def action_apply_qty(self):
        to_apply = self.filtered(lambda x: not x.qty_applied)
        to_apply.force_set_qty_done()

    @api.multi
    def action_back_to_draft(self):
        self.picking_ids.do_unreserve()
        #self.action_assign()
        for batch in self:
            batch.write({'state': 'draft'})


    @api.multi
    def action_print_picking(self):
        if len(self)==1 and self.picking_type_id and self.picking_type_id.code == 'internal':
            return self.env.ref('stock_picking_batch_custom.action_report_batch_picking_custom')
        return super().action_print_picking()

    @api.multi
    def action_assign(self):
        for batch in self:
            for pick in batch.picking_ids:
                pick.action_assign()
            if batch.auto_fill_done:
                batch.mapped('picking_ids').mapped('move_lines').force_set_qty_done(reset=False)

        self.write({'state': 'in_progress'})

        return True

    @api.multi
    def action_transfer(self):
        """ Create wizard to process all active pickings in these batches
        """

        self.ensure_one()
        picks_to_split = self.env['stock.picking']
        precision_digits = self.env[
            'decimal.precision'].precision_get('Product Unit of Measure')
        for batch in self:
            picking_ids = batch.picking_ids
            for picking_id in picking_ids.filtered(lambda x:x.state in ('confirmed', 'assigned')):
                if float_compare(picking_id.quantity_done, 0, precision_digits=precision_digits) == 0:
                    raise ValidationError('El albarán {} no tiene nada realizado. Debes sacarlo de la agrupación o marcar alguna cantidad para hacer'.format(picking_id.name))
            ## Hago el split de todos los albaranes

            #picks_to_split += picking_ids.filtered(lambda x: not x.all_assigned)
            for pick in picking_ids:
                for move in pick.move_lines:
                    if move.product_uom_qty < move.quantity_done:
                        picks_to_split += pick
                        pick.message_post(body='Este albarán se ha sacado de la agrupación {} por una incidencia'.format(batch.name))

            #picks_to_split += picking_ids.filtered(lambda x:  x.all_assigned)
            #picks_to_split.split_process()
        picks_to_split.write({'batch_id': False})
        if self.picking_ids:
            return super().action_transfer()
        else:




        # picks_to_split.write({'batch_id': batch.id})
        # back_domain = [('backorder_id', 'in', picks_to_split.ids)]
        # backorder_ids = self.env['stock.picking'].search(back_domain)
        # backorder_ids.write({'move_type': 'one'})
            action = self.env.ref('stock.action_picking_tree_all').read()[0]
            action['context'] = self._context
            if picks_to_split:
                action['domain'] = [('id', 'in', picks_to_split.ids)]
            else:
                action['domain'] = [('id', 'in', self.picking_ids.ids)]
            return action
