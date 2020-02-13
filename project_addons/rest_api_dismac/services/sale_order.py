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
from odoo.exceptions import ValidationError

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
            "refcli": "%s" % sale_order.uvigo_order if sale_order.uvigo_order else '',
            "precio_total": "{:.2f}".format(sale_order.amount_untaxed),
            "precio_total_iva": "{:.2f}".format(sale_order.amount_total),
            "iva_valor": "{:.2f}".format(sale_order.amount_tax),
            "pdf": "%s" % base64.b64encode(pdf) if pdf else False,
            "observaciones": "%s" % sale_order.observations if sale_order.observations else '',
            "lineas_pedido": []
        }

        if sale_order.order_line:
            for line in sale_order.order_line:
                line_data = {
                    "id": "%s" % line.id,
                    "cantidad": "%s" % line.product_uom_qty,
                    "codigo": "%s" % line.product_id.default_code if line.product_id.default_code else '',
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

    is_from_uvigo = fields.Boolean(compute="_check_owner", compute_sudo=True)
    uvigo_order = fields.Char(string="UVigo order number")
    uvigo_url = fields.Char(string="UVigo order URL")
    uvigo_pdf = fields.Char(string="UVigo order PDF", compute="_compute_urls")
    uvigo_zip = fields.Char(string="UVigo order ZIP", compute="_compute_urls")

    def _compute_urls(self):
        if self.uvigo_url:
            self.uvigo_pdf = "{}/pdf".format(self.uvigo_url)
            self.uvigo_zip = "{}/zip".format(self.uvigo_url)

    def _check_owner(self):
        api_partner_id = self.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_partner', False)
        if api_partner_id:
            api_partner = self.env['res.partner'].browse(int(api_partner_id))
            if not (api_partner == self.partner_id or api_partner == self.partner_id.parent_id):
                self.is_from_uvigo = False
            else:
                self.is_from_uvigo = True
    
    def get_sale_order_for_uvigo(self, datos_pedido, uvigo_url, delivery_partner, invoice_partner):

        api_partner = self.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_partner', False)

        if api_partner:
            api_partner = self.env['res.partner'].browse(int(api_partner))
        else:
            raise ValidationError(_('API partner not defined.'))

        already_an_order = self.check_if_already_an_order(datos_pedido['numero'])

        if already_an_order:
            sale_order = already_an_order
            sale_order.update({
                'partner_id': api_partner.id,
                'partner_invoice_id': invoice_partner.id,
                'partner_shipping_id': delivery_partner.id,
                'uvigo_order': datos_pedido['numero'],
                'observations': datos_pedido['observaciones'],
                'uvigo_url': uvigo_url,
                'commitment_date': datos_pedido['fecha_entrega']
            })

        else:

            sale_order = self.env['sale.order'].new({
                'partner_id': api_partner.id,
                'type_id': 2,   #HARDCODEADO, necesario buscar alternativa
            })
            sale_order.onchange_partner_id()
            sale_order_vals = sale_order._convert_to_write(sale_order._cache)
            sale_order_vals.update({
                'partner_invoice_id': invoice_partner.id,
                'partner_shipping_id': delivery_partner.id,
                'uvigo_order': datos_pedido['numero'],
                'client_order_ref': datos_pedido['numero'],
                'observations': datos_pedido['observaciones'],
                'uvigo_url': uvigo_url,
                'commitment_date': datos_pedido['fecha_entrega'],
                'type_id': 2,    #HARDCODEADO, necesario buscar alternativa
                'team_id': 6    #HARDCODEADO, necesario buscar alternativa
            })
            sale_order = self.env['sale.order'].create(sale_order_vals)
        return sale_order

    def check_if_already_an_order(self, uvigo_order):
        return self.env['sale.order'].search([('uvigo_order', '=', uvigo_order)], limit=1)

    def process_api_lines(self, lineas_detalle):
        if self.order_line:
            _logger.info("Eliminando líneas originales del pedido con id: {}".format(self.id))
            for order_line in self.order_line:
                order_line.unlink()

        for line in lineas_detalle:
            ## SI NO HAY line['codigo_articulo_proveedor'] asociar a 999PAP y mantener descripcion
            if not line['codigo_articulo_proveedor']:
                line['codigo_articulo_proveedor'] = '999PAP'
            product = self.env['product.product'].search([('default_code', '=', line['codigo_articulo_proveedor'])])

            if not product.id:
                _logger.error("No se ha encontrado el producto con default_code: {}.".format(line['codigo_articulo_proveedor']))
                line['codigo_articulo_proveedor'] = '999PAP'
                product = self.env['product.product'].search([('default_code', '=', line['codigo_articulo_proveedor'])])


            
            sale_order_line = self.env['sale.order.line'].new({
                'order_id': self.id,
                'partner_id': self.partner_id.id,
                'product_id': product.id,
                'price_unit': line['precio_unitario'],
                'product_uom': product.uom_id.id,
                'product_uom_qty': line['cantidad'],
            })
            sale_order_line.product_id_change()
            sale_order_line_vals = sale_order_line._convert_to_write(sale_order_line._cache)
            sale_order_line_vals.update({
                'price_unit': line['precio_unitario'],
                'product_uom': product.uom_id.id,
                'product_uom_qty': line['cantidad'],
                'name': line['descripcion'],
            })
            sol = self.env['sale.order.line'].create(sale_order_line_vals)

            _logger.info("Añadiendo {} cantidad(es) de {} al pedido {}.".format(line['cantidad'], product.name, self.id))
            

    def read_json_data(self):
        log_entry = self.env['api.access.log'].sudo().create({
            'access_type': "get",
            'order_id': self.id,
            'error': False,
            'url': "{}/json".format(self.uvigo_url)
        })
        _logger.info("Recuperando datos del pedido con id: {}".format(self.id))
        json_url = "{}/json".format(self.uvigo_url)
        with urllib.request.urlopen(json_url) as url:
            data = json.loads(url.read().decode())

            already_an_order = self.check_if_already_an_order(data['datos_pedido']['numero'])

            if already_an_order:
                _logger.error("El código ({}) de UVigo ya existe en el sistema: Pedido {}.".format(data['datos_pedido']['numero'], already_an_order.name))
                raise ValidationError(_("The UVigo code ({}) is already in the system: Order {}.".format(data['datos_pedido']['numero'], already_an_order.name)))

            self.uvigo_order = data['datos_pedido']['numero']
            self.client_order_ref = data['datos_pedido']['numero']
            self.observations = data['datos_pedido']['observaciones']
            self.commitment_date = data['datos_pedido']['fecha_entrega']
            log_entry.sudo().update({
                'uvigo_order': self.uvigo_order
            })

            delivery_name = data['datos_pedido']['destinatario']
            punto_entrega = data['datos_pedido']['punto_entrega']
            oficina_contable = data['datos_facturacion']['datos_facturacion_dir3']['oficina_contable']
            organo_gestor = data['datos_facturacion']['datos_facturacion_dir3']['organo_gestor']
            unidad_tramitadora = data['datos_facturacion']['datos_facturacion_dir3']['unidad_contratacion']
            unidad_responsable_gasto = data['datos_pedido']['unidad_responsable_gasto']

            delivery_partner = self.env['res.partner'].get_delivery_for_api_partner(delivery_name, punto_entrega)
            self.partner_shipping_id = delivery_partner.id

            invoice_partner = self.env['res.partner'].get_invoice_for_api_partner(unidad_responsable_gasto, oficina_contable,
                            organo_gestor, unidad_tramitadora, delivery_name, punto_entrega)
            self.partner_invoice_id = invoice_partner.id

            if data['lineas_detalle']:                
                self.process_api_lines(data['lineas_detalle'])