# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):

    _inherit = "sale.order.line"

    def action_show_accessory_products(self):
        self.ensure_one()
        view = self.env.ref('accessory_product.view_accessory_product_ids')
        if not self.product_id:
            return
        action = {
            'name': _('accessory products'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.accessory.wzd',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
        }

        return action

    def get_price_for_product(self, product_id):

        product = product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty or 1,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom = product_id.uom_id.id
        )
        if self.order_id.pricelist_id and self.order_id.partner_id:
            lst_price = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        else:
            lst_price = product.lst_price
        return lst_price

