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

class SaleOrderService(Component):
    _inherit = "base.rest.service"
    _name = "sale.order.service"
    _usage = "sale.order"
    _collection = "base.rest.uvigo.services"
    _description = """
        Sale order Services
        Access to the sale order is only allowed to authenticated users.
        If you are not authenticated go to <a href='/web/login'>Login</a>
    """

    def get(self, _id):
        """
        Get sale order's informations
        """
        return self._to_json(self._get(_id))

    def _get(self, _id):
        return self.env["sale.order"].sudo().browse(_id)

    def _to_json(self, sale_order):

        _logger.info("Solicitud a través de API del pedido con id: {}".format(sale_order.id))

        pdf = self.env.ref('sale.action_report_saleorder').sudo().render_qweb_pdf([sale_order.id])[0] or False

        res = {
            "id": "%s" % sale_order.id,
            "id_ente": "%s" % sale_order.partner_id.parent_id.id,
            "id_usuario": "%s" % sale_order.partner_id.id,
            "nombre": "%s" % sale_order.partner_id.name,
            "fecha": "%s" % sale_order.date_order.strftime("%Y%m%d%H%M%S"),
            "refcli": "%s" % sale_order.uvigo_order or '',
            "precio_total": "{:.2f}".format(sale_order.amount_untaxed),
            "precio_total_iva": "{:.2f}".format(sale_order.amount_total),
            "iva_valor": "{:.2f}".format(sale_order.amount_tax),
            "pdf": "%s" % base64.b64encode(pdf) if pdf else False,
            "observaciones": "%s" % sale_order.observations,
            "lineas_pedido": []
        }

        if sale_order.order_line:
            for line in sale_order.order_line:
                line_data = {
                    "id": "%s" % line.id,
                    "cantidad": "%s" % line.product_uom_qty,
                    "codigo": "%s" % line.product_id.default_code,
                    "importe": "{:.4f}".format(line.price_subtotal),
                    "precio": "{:.4f}".format(line.price_total),
                    "iva_porcentaje": "{:.2f}".format(line.tax_id.amount),
                    "iva_valor": "{:.4f}".format(line.price_tax),
                    "descripcion": "%s" % line.product_id.display_name
                }
                res["lineas_pedido"].append(line_data)
        return res


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_from_uvigo = fields.Boolean(compute="_check_owner")   
    uvigo_order = fields.Char(string="UVigo order number")
    uvigo_url = fields.Char(string="UVigo order URL")
    uvigo_pdf = fields.Char(string="UVigo order PDF", compute="_compute_urls")
    uvigo_zip = fields.Char(string="UVigo order ZIP", compute="_compute_urls")

    def _compute_urls(self):
        if self.uvigo_url:
            self.uvigo_pdf = "{}/pdf".format(self.uvigo_url)
            self.uvigo_zip = "{}/pdf".format(self.uvigo_url)

    def _check_owner(self):
        api_partner_id = self.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_partner', False)
        if api_partner_id:
            api_partner = self.env['res.partner'].browse(int(api_partner_id))
            if not (api_partner == self.partner_id or api_partner == self.partner_id.parent_id):
                self.is_from_uvigo = False
            else:
                self.is_from_uvigo = True

    def read_json_data(self):
        _logger.info("Recuperando datos del pedido con id: {}".format(self.id))
        json_url = "{}/json".format(self.uvigo_url)
        with urllib.request.urlopen(json_url) as url:
            data = json.loads(url.read().decode())
            self.uvigo_order = data['datos_pedido']['numero']
            self.observations = data['datos_pedido']['observaciones']

            if data['lineas_detalle']:
                _logger.info("Eliminando líneas originales del pedido con id: {}".format(self.id))
                for order_line in self.order_line:
                    order_line.unlink()

            for line in data['lineas_detalle']:

                product = self.env['product.product'].search([('default_code', '=', line['codigo_articulo_proveedor'])])
                
                sale_order_line = self.env['sale.order.line'].create({
                    'order_id': self.id,
                    'partner_id': self.partner_id,
                    'product_id': product.id,
                    'price_unit': line['precio_unitario'],
                    'product_uom': product.uom_id.id,
                    'product_uom_qty': line['cantidad'],
                    'name': line['descripcion'],
                })

                _logger.info("Añadiendo {} cantidad(es) de {} al pedido {}.".format(line['cantidad'], product.name, self.id))