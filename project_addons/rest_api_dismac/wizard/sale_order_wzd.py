# -*- coding: utf-8 -*-
#
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#
##############################################################################
#
#    Copyright (C) 2018 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
#    Vicente Ángel Gutiérrez Fernández <vicente@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64, logging, urllib.request, json
from odoo.addons.component.core import Component
from odoo import fields, models, _

_logger = logging.getLogger(__name__)

class SaleOrderWzd(models.TransientModel):

    _name = "sale.order.wzd"

    uvigo_url = fields.Char(string="UVigo order URL")

    def read_json_data(self):
        log_entry = self.env['api.access.log'].sudo().create({
            'access_type': "get",
            'error': False,
            'url': "{}/json".format(self.uvigo_url)
        })

        _logger.info("Recuperando datos del pedido desde URL: {}".format(self.uvigo_url))
        json_url = "{}/json".format(self.uvigo_url)

        api_partner = self.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_partner', False)

        if api_partner:
            api_partner = self.env['res.partner'].browse(int(api_partner))

        with urllib.request.urlopen(json_url) as url:

            data = json.loads(url.read().decode())

            new_sale_order = self.env['sale.order'].create({
                'partner_id': api_partner.id,
                'partner_invoice_id': api_partner.id,
                'partner_shipping_id': api_partner.id,
                'uvigo_order': data['datos_pedido']['numero'],
                'observations': data['datos_pedido']['observaciones']
            })

            log_entry.sudo().update({
                'order_id': new_sale_order.id,
                'uvigo_order': data['datos_pedido']['numero']
            })
            
            if data['lineas_detalle']:
                for line in data['lineas_detalle']:

                    product = self.env['product.product'].search([('default_code', '=', line['codigo_articulo_proveedor'])])
                    
                    sale_order_line = self.env['sale.order.line'].create({
                        'order_id': new_sale_order.id,
                        'partner_id': new_sale_order.partner_id,
                        'product_id': product.id,
                        'price_unit': line['precio_unitario'],
                        'product_uom': product.uom_id.id,
                        'product_uom_qty': line['cantidad'],
                        'name': line['descripcion'],
                    })

                    _logger.info("Añadiendo {} cantidad(es) de {} al pedido {}.".format(line['cantidad'], product.name, new_sale_order.id))