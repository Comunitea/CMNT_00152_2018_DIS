# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):

    _inherit = "sale.order"

    def action_show_suggested_products(self):
        self.ensure_one()
        view = self.env.ref('suggested_product.view_suggested_product_ids')
        if not self.product_id:
            return
        action = {
            'name': _('suggested products'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.suggested.wzd',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
        }

        return action

    def get_price_for_suggested_product(self, product_id, uom_id):
        vals = {
            'order_id': self.id,
            'product_id': product_id.id,
            'uom_id': uom_id
        }
        new_line = self.env['sale.order.line'].new(vals)
        new_line.product_id_change()
        return new_line.price_unit


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    from_suggested= fields.Boolean('From suggested')