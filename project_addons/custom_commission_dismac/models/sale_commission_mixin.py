# © 2016 Nicola Malcontenti - Agile Business Group
# © 2016 Davide Corio - Abstract
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields


class SaleCommissionLineMixin(models.AbstractModel):
    _inherit = 'sale.commission.line.mixin'

    reduction_per = fields.Float(
        '% Over subtotal', default=100.0,
        help='Compute settlement with % reduced over invoices subtotal')

    def _get_commission_amount(self, commission, subtotal, product, quantity):
        """Get the commission amount for the data given. To be called by
        compute methods of children models.
        """
        self.ensure_one()
        if commission.commission_type == 'goal':
            return 0.0
        return super()._get_commission_amount(
            commission, subtotal, product, quantity,
        )
