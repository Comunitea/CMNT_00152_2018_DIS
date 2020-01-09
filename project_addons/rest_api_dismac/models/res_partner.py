# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2019 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
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

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"

    def get_delivery_for_api_partner(self, delivery_name, delivery_street):

        api_partner = self.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_partner', False)

        if api_partner:
            api_partner = self.env['res.partner'].browse(int(api_partner))
        else:
            raise ValidationError(_('API partner not defined.'))

        delivery_partner = self.env['res.partner'].search([
            ('name', '=', delivery_name),
            ('street', '=', delivery_street),
            ('zip_id', '=', api_partner.zip_id.id)
        ], limit=1)

        if not delivery_partner:

            delivery_partner = self.env['res.partner'].create({
                'name': delivery_name, 
                'active': False,
                'parent_id': api_partner.id,
                'type': 'delivery',
                'street': delivery_street,
                'street2': api_partner.street,
                'city': api_partner.city,
                'state_id': api_partner.state_id.id,
                'country_id': api_partner.country_id.id,
                'zip': api_partner.zip
            })
        
        return delivery_partner


    def get_invoice_for_api_partner(self, delivery_street, oficina_contable, organo_gestor, unidad_tramitadora):

        api_partner = self.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_partner', False)

        if api_partner:
            api_partner = self.env['res.partner'].browse(int(api_partner))
        else:
            raise ValidationError(_('API partner not defined.'))

        invoice_partner = self.env['res.partner'].search([
            ('oficina_contable', '=', oficina_contable),
            ('organo_gestor', '=', organo_gestor),
            ('unidad_tramitadora', '=', unidad_tramitadora)
        ], limit=1)

        if not invoice_partner:

            invoice_partner = self.env['res.partner'].create({
                'name': api_partner.name, 
                'active': False,
                'parent_id': api_partner.id,
                'type': 'invoice',
                'street': delivery_street,
                'street2': api_partner.street,
                'city': api_partner.city,
                'state_id': api_partner.state_id.id,
                'country_id': api_partner.country_id.id,
                'zip': api_partner.zip,
                'vat': api_partner.vat,
                'oficina_contable': oficina_contable,
                'organo_gestor': organo_gestor,
                'unidad_tramitadora': unidad_tramitadora,
                'facturae': True
            })

        return invoice_partner