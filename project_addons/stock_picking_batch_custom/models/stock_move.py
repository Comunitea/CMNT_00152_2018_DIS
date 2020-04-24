# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

class StockMove(models.Model):

    _inherit = "stock.move"


    @api.multi
    def action_new_move_line(self):

        vals = self._prepare_move_line_vals(quantity=0)
        vals['not_stock'] = self.product_uom_qty - self.reserved_availability
        ml = self.env['stock.move.line'].create(vals)
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
            "res_id": self._context.get('from_group_line_id', False),
            "context": dict(
                self.env.context,
            ),
        }

class StockMoveLine(models.Model):

    _inherit = "stock.move.line"

    sale_order = fields.Many2one(related='move_id.sale_line_id.order_id')
    partner_id = fields.Many2one(related='move_id.partner_id')
    p_color = fields.Char('COlor', compute='get_p_color')

    not_stock = fields.Float('Not Reserved', default=0.0, digits=dp.get_precision('Product Unit of Measure'), required=True)
    product_qty_by_location = fields.Float('C. en la ubicación', compute="compute_product_qty_by_location")
    # sale_line_id = fields.Many2one(related='move_id.sale_line_id', string='Venta')
    src_removal_priority = fields.Integer(related='location_id.removal_priority', store=True)
    dest_removal_priority = fields.Integer(related='location_dest_id.removal_priority', store=True)
    # ordered_qty = fields.Float(string="C. Ordenada", compute="_get_ordered_qty")
    # empty_line = fields.Boolean('Creada vacía')


    @api.multi
    def apply_reserved_to_done_qties(self):
        for line in self:
            line.qty_done = line.product_uom_qty + line.not_stock

    @api.multi
    def action_delete_move_line(self):
        self.unlink()
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
            "res_id": self._context.get('from_group_line_id', False),
            "context": dict(
                self.env.context,
            ),
        }

    @api.multi
    def write(self, vals):
        return super().write(vals=vals)

    @api.multi
    def compute_product_qty_by_location(self):
        for line in self:
            quants =  self.env['stock.quant']._gather(line.product_id, line.location_id)
            line.product_qty_by_location = sum((x.quantity - x.reserved_quantity) for x in quants) + line.product_uom_qty

    @api.multi
    def get_p_color(self):
        for line in self:
            if line.qty_done == line.product_uom_qty:
                p_color = '10' #green
            elif line.qty_done > 0 and line.qty_done != line.product_uom_qty:
                p_color = '1' #red
            else:
                p_color = '4' #light blue
            line.p_color = p_color


    @api.multi
    def action_change_qty(self):
        inc = self._context.get('inc', False)
        if inc == 1:
            self.qty_done += inc
        elif inc==-1:
            self.qty_done = max(0, self.qty_done + inc)

