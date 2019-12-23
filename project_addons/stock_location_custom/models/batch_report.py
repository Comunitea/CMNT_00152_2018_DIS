# Copyright 2018 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models
from odoo.tools import float_is_zero


_logger = logging.getLogger(__name__)


class ReportPrintBatchPicking(models.AbstractModel):
    _inherit = 'report.stock_picking_batch_extended.report_batch_picking'


    @api.model
    def new_level_1(self, operation):
        return {
            'product': operation.product_id,
            'product_qty': not float_is_zero(operation.product_qty, precision_rounding=2)
            or operation.qty_done,
            'operations': operation,
        }