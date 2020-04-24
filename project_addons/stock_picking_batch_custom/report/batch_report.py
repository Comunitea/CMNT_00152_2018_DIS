# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models
from odoo import tools

_logger = logging.getLogger(__name__)

class ReportPrintBatchPicking(models.AbstractModel):
    _name = "report.stock_picking_batch_custom.report_batch_picking_custom"

    @api.model
    def key_level_0(self, operation):
        return (
            operation.location_id.location_id.id,
            operation.location_dest_id.id,
        )

    @api.model
    def key_level_1(self, operation):
        return operation.location_id.location_id.id, operation.product_id.id

    @api.model
    def new_level_0(self, operation):
        destino = '{}/{}'.format(
                operation.location_dest_id.location_id.location_id.name,
                operation.location_dest_id.location_id.name,
            )
        origen = '{}/{}'.format(
                operation.location_id.location_id.location_id.name,
                operation.location_id.location_id.name,
            )
        if operation.move_id.picking_type_id.code == 'incoming':
            order = operation.location_dest_id.removal_priority
            level_0_name = u"\u21E8 {}".format(destino)

        elif operation.move_id.picking_type_id.code == 'outgoing':
            order = operation.location_id.removal_priority
            level_0_name = u"{} \u21E8".format(origen)
        else:
            order = operation.location_id.removal_priority
            level_0_name = u"{} \u21E8 {}".format(origen, destino)
        return {
            "name": level_0_name,
            "location": operation.location_id,
            "location_dest": operation.location_dest_id,
            "order": order,
            "l1_items": {},
        }

    @api.model
    def new_level_1(self, operation):
        if operation.move_id.picking_type_id.code == 'incoming':
            order = operation.location_dest_id.removal_priority
        else:
            order = operation.location_id.removal_priority
        return {
            'location_id': operation.move_id.location_id,
            'order': order,
            "product": operation.product_id,
            'lot_id': operation.lot_id,
            'package_id': operation.package_id,
            "product_qty": operation.product_qty or operation.qty_done,
            "product_uom_qty": operation.product_uom_qty,
            "operations": operation,
            "move_ordered_qty": operation.move_id.product_uom_qty,
            "other_moves": "*" * len(operation.move_id.move_line_ids),
            "state": operation.move_id.state
        }


    @api.model
    def update_level_1(self, group_dict, operation):
        def get_state(val, val1):

            if val1 == 'partially_available':
                return val1
            if val1 == 'assigned':
                return val
            if val1 == 'confirmed':
                if val == 'partially_available' or val == 'assigned':
                    return val
                else:
                    return val1
            if val1=='state':
                if val != 'cancel' and val != 'draft':
                    return val
            return val1
            raise ValueError('No encontrado para {} y {}'.format(val, val1))


        group_dict["product_qty"] += operation.product_uom_qty or operation.qty_done
        group_dict["product_uom_qty"] += operation.product_uom_qty
        group_dict["operations"] += operation
        group_dict["state"] = get_state(group_dict["state"], operation.move_id.state)

    @api.model
    def sort_level_0(self, rec_list, location_field="location"):
        return sorted(
            rec_list,
            key=lambda rec: (
                rec['order']
            ),
        )

        return sorted(
            rec_list,
            key=lambda rec: (
                rec[location_field].posx,
                rec[location_field].posy,
                rec[location_field].posz,
                rec[location_field].name,
            ),
        )

    @api.model
    def sort_level_1(self, rec_list, product_field="product"):
        return sorted(
            rec_list,
            key=lambda rec: (
                rec['order'],
                rec[product_field].default_code or "",
                rec[product_field].id,
            ),
        )

    @api.model
    def _get_no_stock(self, batch):
        moves = batch.move_lines.filtered(lambda x: x.product_uom_qty != x.reserved_availability)
        #print (moves)
        return moves


    @api.model
    def get_ordered_qties(self, batch):
        poq = {}
        for ml in batch.mapped('move_lines'):
            id = str(ml.product_id.id)
            if id in poq.keys():
                poq[id] += ml.product_uom_qty
            else:
                poq[id] = ml.product_uom_qty
        print (poq)
        return poq

    @api.model
    def get_product_moves(self, batch):
        mlxp = {}
        for ml in batch.mapped('move_line_ids'):
            id = str(ml.product_id.id)
            if id in mlxp.keys():
                mlxp[id] |= ml
            else:
                mlxp[id] = ml
        print(mlxp)
        return mlxp

    @api.model
    def _get_grouped_data(self, batch):

        grouped_data = {}
        for op in batch.move_line_ids:
            l0_key = self.key_level_0(op)
            if l0_key not in grouped_data:
                grouped_data[l0_key] = self.new_level_0(op)
            l1_key = self.key_level_1(op)
            if l1_key in grouped_data[l0_key]["l1_items"]:
                self.update_level_1(
                    grouped_data[l0_key]["l1_items"][l1_key], op
                )
            else:
                grouped_data[l0_key]["l1_items"][l1_key] = self.new_level_1(op)
        for l0_key in grouped_data.keys():
            grouped_data[l0_key]["l1_items"] = self.sort_level_1(
                grouped_data[l0_key]["l1_items"].values()
            )
        return self.sort_level_0(grouped_data.values())

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
            "get_grouped_data": self._get_grouped_data,
            'moves': self._get_no_stock(docs),
            "now": fields.Datetime.now,
            "ordered_qties": self.get_ordered_qties(docs),
            "product_moves": self.get_product_moves(docs)
        }
