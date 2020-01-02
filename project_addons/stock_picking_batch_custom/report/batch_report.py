# Copyright 2018 Tecnativa - Carlos Dauden
# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models


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
        level_0_name = u"{} \u21E8 {}".format(
            operation.location_id.location_id.name,
            operation.location_dest_id.name,
        )
        if operation.move_id.picking_type_id.code == 'incoming':
            order = operation.location_dest_id.removal_priority
        else:
            order = operation.location_id.removal_priority
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
        }

    @api.model
    def update_level_1(self, group_dict, operation):
        group_dict["product_qty"] += operation.product_qty or operation.qty_done
        group_dict["product_uom_qty"] += operation.product_uom_qty
        group_dict["operations"] += operation

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
        return {
            "doc_ids": docids,
            "doc_model": model,
            "data": data,
            "docs": docs,
            "get_grouped_data": self._get_grouped_data,
            "now": fields.Datetime.now,
        }
