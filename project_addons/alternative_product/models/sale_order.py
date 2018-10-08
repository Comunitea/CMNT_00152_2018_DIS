# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):

    _inherit = "sale.order.line"

    def action_show_alternative_products(self):
        self.ensure_one()
        view = self.env.ref('alternative_product.view_alternative_product_ids')
        if not self.product_id:
            return
        action = {
            'name': _('Alternative products'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.alternative.wzd',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
        }

        return action

