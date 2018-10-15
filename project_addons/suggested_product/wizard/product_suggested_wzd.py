# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp


class ProductSuggestedVariantWzd(models.TransientModel):

    _name = 'product.suggested.variant.wzd'

    wzd_id = fields.Many2one('product.suggested.wzd')
    display_name = fields.Char('Display name', readonly=True)
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    uom_id = fields.Many2one('product.uom', string='uom_id', readonly=True)
    selected = fields.Boolean('selected', default=False)

    default_code = fields.Char('Default code', readonly=True)
    lst_price = fields.Float('Public Price', digits=dp.get_precision('Product Price'), readonly=True)
    avg_price_unit = fields.Float('Avg Price', digits=dp.get_precision('Product Price'), readonly=True)
    max_price_unit = fields.Float('Max Price', digits=dp.get_precision('Product Price'), readonly=True)
    min_price_unit = fields.Float('Min Price', digits=dp.get_precision('Product Price'), readonly=True)

    same_client = fields.Boolean("Same client", readonly=True)
    #image_small = fields.Binary("image_small", readonly=True)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', readonly=True)
    qty_available = fields.Float(
        'Quantity On Hand',
        digits=dp.get_precision('Product Unit of Measure'), readonly=True)

    avg_uom_qty = fields.Float('Avg Line Qty', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    max_uom_qty = fields.Float('Max Line Qty', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    min_uom_qty = fields.Float('Min Line Qty', digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    line_count = fields.Integer('Line count', readonly=True)

    p_id = fields.Integer(related="product_id.id", readonly=True)
    product_qty = fields.Float('Quantity to add', digits=dp.get_precision('Product Unit of Measure'))


    @api.multi
    def set_as_selected(self):
        if self._context.get('new_product_id', False):
            ol = self.env['sale.order.line'].browse(self._context.get('default_sale_order_line_id'))
            product_uom_qty = ol.product_uom_qty
            ol.product_id = self._context.get('new_product_id')
            ol.product_id_change()
            ol.product_uom_qty = product_uom_qty
            ol.product_uom_change()

class ProductSuggestedWzd(models.TransientModel):

    _name = 'product.suggested.wzd'

    sale_order_id = fields.Many2one('sale.order', string='Sale order')
    suggested_product_ids = fields.Many2many('product.suggested.variant.wzd', string='suggested product')
    total_amount = fields.Monetary(string='Untaxed Amount', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    same_client_product_ids = fields.Many2many('product.suggested.variant.wzd', string='suggested product')
    #not_same_client_product_ids = fields.Many2many(related='suggested_product_ids', domain="[('same_client','!=',True)]", readonly=True)


    def action_add_suggested_products(self):
        import ipdb; ipdb.set_trace()
        self.selected = True

    @api.model
    def get_values(self, sale_order_id, product_ids=False, partner_id=False):

        if not product_ids or not partner_id:
            return False

        suggested_ids = self.get_suggested_ids(product_ids, partner_id, sale_order_id.id)
        vals = []
        vals_client= []
        for line in suggested_ids:

            product = self.env['product.product'].browse(line['product_id'])
            line.update({'lst_price': sale_order_id.get_price_for_suggested_product(product, line['uom_id']),
                         'display_name': product.display_name,
                         'qty_available': product.qty_available,
                         'currency': sale_order_id.currency_id.id,
                         'default_code': product.default_code})

            if line['same_client'] == 1:
                vals_client.append((0,0, line))
            else:
                vals.append((0, 0, line))
            print ("\nLinea de datos\n")
            print(line)

        return {'suggested_product_ids': vals,
                'same_client_product_ids': vals_client}

    @api.model
    def default_get(self, fields):

        res = super(ProductSuggestedWzd, self).default_get(fields)
        domain = [('order_id','=', res['sale_order_id'])]
        sale_order_id = self.env['sale.order'].browse(res['sale_order_id'])
        line_ids = self.env['sale.order.line'].search_read(domain, ['product_id'])
        product_ids = [line['product_id'][0] for line in line_ids]

        print("\nres\n")
        print (res)

        return res

    @api.model
    def set_as_selected(self):

        me = self._context


        return True

    def change_sale_order_line(self):
        return True



    def get_suggested_ids(self, product_ids, partner_id, order_id, cte=2):

        select  ="select pp.id as product_id, count(sol.product_id) as line_count, " \
                 "avg(sol.product_uom_qty) as avg_uom_qty, max(sol.product_uom_qty) as max_uom_qty, sum(sol.product_uom_qty) as min_uom_qty, " \
                 "avg(sol.price_unit) as avg_price_unit, max(sol.price_unit) as max_price_unit, min(sol.price_unit) as min_price_unit, " \
                 "same_client as same_client, sa" \
                 "me_client * {} * count(sol.product_id) + count(sol.product_id) as ord, " \
                 "sol.product_uom as uom_id  " \
                 "from sale_order_line sol " \
                 "join sale_order so on so.id = sol.order_id " \
                 "join product_product pp on sol.product_id = pp.id " \
                 "join(select id, (partner_id = {})::int as same_client from sale_order) sob on sob.id = sol.order_id ".format(cte, partner_id)
        if len(product_ids)>1:
            where = "where sol.order_id in (select order_id from sale_order_line where product_id in {}) and product_id not in {} ".format(tuple(product_ids), tuple(product_ids))
        else:
            where = "where sol.order_id in (select order_id from sale_order_line where product_id = {}) and product_id != {} ".format(product_ids[0], product_ids[0])

        order = "group by pp.id, same_client, sol.product_uom " \
                "order by same_client * {} * count(sol.product_id) + count(sol.product_id) desc, sum(sol.product_uom_qty) desc ".format(cte)

        new_select = "union {}".format(select)
        new_where = "where sol.order_id = {}".format(order_id)

        sql = "{} {} {}".format(select, where, order)
        print (sql)
        self.env.cr.execute(sql)
        lines = self.env.cr.dictfetchall()
        return lines



