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

    def get_delivery_for_api_partner(self, delivery_name, punto_entrega):

        api_partner = self.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_partner', False)

        if api_partner:
            api_partner = self.env['res.partner'].browse(int(api_partner))
        else:
            raise ValidationError(_('API partner not defined.'))

        lastname, name = delivery_name.split(', ')

        delivery_partner = self.env['res.partner'].search([
            '|',
            ('active', '=', True),
            ('active', '=', False),
            ('firstname', '=', name),
            ('lastname', '=', lastname),
            ('street', '=', punto_entrega['centro']),
            ('street2', '=', punto_entrega['campus'])
        ], limit=1)

        if not delivery_partner:

            delivery_partner = self.env['res.partner'].create({
                'firstname': name, 
                'lastname': lastname, 
                'active': False,
                'parent_id': api_partner.id,
                'type': 'delivery',
                'street': punto_entrega['centro'],
                'street2': punto_entrega['campus']
            })
        
        return delivery_partner


    def get_invoice_for_api_partner(self, unidad_responsable_gasto, oficina_contable, organo_gestor, unidad_tramitadora, delivery_name, punto_entrega):

        api_partner = self.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_partner', False)

        if api_partner:
            api_partner = self.env['res.partner'].browse(int(api_partner))
        else:
            raise ValidationError(_('API partner not defined.'))

        # invoice_partner = self.env['res.partner'].search([
        #     ('oficina_contable', '=', oficina_contable),
        #     ('organo_gestor', '=', organo_gestor),
        #     ('unidad_tramitadora', '=', unidad_tramitadora),
        #     ('parent_id', '=' , api_partner.id), 
        # ], limit=1)

        #if not invoice_partner:

        invoice_partner = self.env['res.partner'].create({
            'name': unidad_responsable_gasto, 
            'vat': api_partner.vat,
            'country_id': api_partner.country_id.id,
            'state_id': api_partner.state_id.id,
            'active': True,
            'parent_id': api_partner.id,
            'type': 'invoice',
            'oficina_contable': oficina_contable,
            'organo_gestor': organo_gestor,
            'unidad_tramitadora': unidad_tramitadora,
            'facturae': True,
            'street': delivery_name,
            'street2': punto_entrega['centro'] + "- " + punto_entrega['campus'],
            'customer_invoice_transmit_method_id': 1,  #HARDCODEADO... deberíamos buscar solución alternativa"
            'invoice_integration_method_ids': [(6,0,[2])]
        })

        return invoice_partner