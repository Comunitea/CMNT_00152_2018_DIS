# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductAlternativeVariantWzd(models.TransientModel):

    _name = 'product.alternative.variant.wzd'

    wzd_id = fields.Many2one('product.alternative.wzd')
    name = fields.Char('product_id.display_name')
    product_id = fields.Many2one('product.product')
    selected = fields.Boolean('selected', default=False)
    default_code = fields.Char('product_id.default_code')
    lst_price = fields.Float('product_id.lst_price')
    image_small = fields.Binary(related="product_id.image_small")
    currency_id = fields.Many2one(related='product_id.currency_id')
    catalogue_code = fields.Char('catalogue_code')
    qty_available = fields.Float(related='product_id.qty_available')
    virtual_available = fields.Float(related='product_id.virtual_available')
    p_id = fields.Integer("product_id")

    @api.multi
    def set_as_selected(self):
        if self._context.get('new_product_id', False):
            ol = self.env['sale.order.line'].browse(self._context.get('default_sale_order_line_id'))
            product_uom_qty = ol.product_uom_qty
            ol.product_id = self._context.get('new_product_id')
            ol.product_id_change()
            ol.product_uom_qty = product_uom_qty
            ol.product_uom_change()

class ProductAlternativeWzd(models.TransientModel):

    _name = 'product.alternative.wzd'

    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale order line')
    product_id = fields.Many2one('product.product', string='Product')
    alternative_product_ids = fields.Many2many('product.alternative.variant.wzd', string='Alternative product', readonly="1")
    default_code = fields.Char(related='product_id.default_code', readonly="1")
    lst_price = fields.Float(related='product_id.lst_price', readonly="1")
    image_medium = fields.Binary(related='product_id.image_medium')
    catalogue_code = fields.Char(related='product_id.catalogue_code', readonly="1")
    qty_available = fields.Float(related='product_id.qty_available', readonly="1")
    virtual_available = fields.Float(related='product_id.virtual_available', readonly="1")
    p_id = fields.Integer("product_id")

    @api.model
    def get_values(self, product_id=False):

        if not product_id:
            return False
        product_alternative_ids = []
        alternative_ids = product_id.alternative_product_ids.mapped('product_variant_ids')
        return {'p_id': product_id.id,
                'product_id': product_id.id,
                'sale_order_line_id' : self._context.get('default_sale_order_line_id'),
                'alternative_product_ids': [(0, 0, {'product_id': alternative.id,
                                                    'display_name': alternative.display_name,
                                                    'default_code': alternative.default_code,
                                                    'p_id': alternative.id,
                                                    #'wzd_id': self.id,
                                                    'name': alternative.display_name,
                                                    'lst_price': alternative.lst_price}) for alternative in alternative_ids]
                }

    @api.model
    def default_get(self, fields):
        res = super(ProductAlternativeWzd, self).default_get(fields)
        product_id = self.env['product.product'].browse(self._context.get('default_product_id'))
        res.update(self.get_values(product_id))
        print (res)
        return res

    @api.model
    def set_as_selected(self):

        me = self._context


        return True

    def change_sale_order_line(self):
        return True
