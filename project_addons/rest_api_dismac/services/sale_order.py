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

import base64
from odoo.addons.component.core import Component
from odoo import _


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

        pdf = self.env.ref('sale.action_report_saleorder').sudo().render_qweb_pdf([sale_order.id])[0] or False

        res = {
            "id": "%s" % sale_order.id,
            "id_ente": "%s" % sale_order.partner_id.parent_id.id,
            "id_usuario": "%s" % sale_order.partner_id.id,
            "nombre": "%s" % sale_order.partner_id.name,
            "fecha": "%s" % sale_order.date_order.strftime("%Y%m%d%H%M%S"),
            # "refcli": ref del pedido en el sistema de UVigo // Opcional
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