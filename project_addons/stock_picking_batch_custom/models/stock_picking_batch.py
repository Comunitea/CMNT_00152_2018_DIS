# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models

from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp


class BatchPickingGroupMove(models.Model):

    _name = "batch.picking.group.move"

    group_product_id = fields.Many2one(
        "product.product", string="Product", store=False
    )
    product_id = fields.Many2one(
        "product.product", string="Product", readonly=True
    )
    qty_done = fields.Float(digits=dp.get_precision("Product Unit of Measure"))
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

    @api.multi
    def action_apply_qties(self):

        if self.qty_done == sum(x.product_uom_qty for x in self.move_line_ids):
            for move_line in self.move_line_ids:
                move_line.qty_done = move_line.product_uom_qty
        else:
            moves_sorted = self.move_line_ids.sorted(
                lambda x: x.sale_order.date_order
            )
            qty_available = self.qty_done
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
                self.env.context,
                show_lots_m2o=move_id.has_tracking != "none",
                show_lots_text=move_id.has_tracking != "none"
                and self.batch_id.picking_type_id.use_create_lots
                and not self.batch_id.picking_type_id.use_existing_lots,
                show_source_location=self.location_id.child_ids,
                show_destination_location=self.location_dest_id.child_ids,
                show_package=not self.location_id.usage == "supplier",
                show_reserved_quantity=move_id.state != "done",
            ),
        }


class StockBatchPicking(models.Model):

    _inherit = "stock.picking.batch"

    @api.depends("picking_ids.picking_type_id")
    @api.multi
    def _get_picking_type(self):
        for batch in self:
            batch.picking_type_id = (
                batch.picking_ids
                and batch.picking_ids[0].picking_type_id
                or False
            )

    def get_move_done(self):

        data = self.env[
            "report.stock_picking_batch_custom.report_batch_picking_custom"
        ]._get_grouped_data(self)

        for pasillo in data:
            for item in pasillo["l1_items"]:
                product_uom_qty = item["product_uom_qty"]
                op_ids = item["operations"].ids
                operations = [(6, 0, op_ids)]
                product_id = item["product"].id
                location_id = item["operations"][0].location_id.id
                val = {
                    "qty_done": 0,
                    "move_line_ids": operations,
                    "product_id": product_id,
                    "location_id": location_id,
                    "product_uom_qty": product_uom_qty,
                    "group": True,
                    "batch_id": self.id,
                }
                self.move_grouped_ids.create(val)

        self.moves_all_count = len(self.move_grouped_ids)
        return

    picking_type_id = fields.Many2one("stock.picking.type", "Picking type")
    move_grouped_ids = fields.One2many(
        "batch.picking.group.move", "batch_id", domain=[("group", "=", True)]
    )
    moves_all_count = fields.Integer("Moves count")
    qty_applied = fields.Boolean(default=False)

    @api.model
    def sort_level_0(self, items, location_field="location_id"):
        # OJO !!!!!! Mismo ordenamiento que la función en batch_report

        res = sorted(
            items,
            key=lambda item: (
                item[location_field].posx,
                item[location_field].posy,
                item[location_field].posz,
                item[location_field].name,
            ),
        )

        return res

    @api.multi
    def get_moves_done(self):
        for batch in self.filtered(lambda x: x.moves_all_count == 0):
            self.get_move_done()
            self.moves_all_count = len(batch.move_grouped_ids)

        return

    @api.multi
    def action_get_moves_done(self):
        self.ensure_one()
        if not self.moves_all_count:
            self.get_move_done()
        view_tree = self.env.ref(
            "stock_picking_batch_custom.view_stock_group_move_tree_operations"
        )
        view_form = self.env.ref(
            "stock_picking_batch_custom.view_stock_group_move_operations"
        )
        return {
            "name": _("Detailed Operations"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "tree",
            "res_model": "batch.picking.group.move",
            "views": [(view_tree.id, "tree"), (view_form.id, "form")],
            "view_id": view_tree.id,
            "domain": [("batch_id", "=", self.id)],
            "context": dict(self.env.context),
        }

    @api.constrains("picking_ids")
    def _check_type(self):
        if len(self.picking_ids.mapped("picking_type_id")) > 1:
            raise ValidationError(_("All pickings in batch must be same type"))

    @api.multi
    def action_group(self):
        self.get_moves_done()

    @api.multi
    def action_cancel_group(self):
        if all(not x.qty_done for x in self.move_grouped_ids):
            self.move_grouped_ids.mapped("move_line_ids").write(
                {"qty_done": 0.00}
            )
            self.move_grouped_ids.unlink()
            self.moves_all_count = len(self.move_grouped_ids)

    @api.multi
    def action_apply_qty(self):
        for batch in self.filtered(lambda x: not x.qty_applied):
            for move in batch.move_grouped_ids:
                move.action_apply_qties()
            batch.qty_applied = True

    @api.multi
    def set_qty_done(self):
        for move in self.move_grouped_ids:
            move.qty_done = move.product_uom_qty
            move.action_apply_qties()
        self.qty_applied = False

    @api.multi
    def reset_qty_done(self):
        for move in self.move_grouped_ids:
            move.qty_done = 0
            move.move_line_ids.write({"qty_done": 0.00})
        self.qty_applied = False
