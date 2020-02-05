# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2019 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
#    Vicente Ángel Gutiérrez <vicente@comunitea.com>
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

from odoo import fields, models, api, _

class DeliveryCarrier(models.Model):

    _inherit = 'delivery.carrier'

    AUTORADIO_SERVICES = [
        ('05', 'MDIA'),
        ('10', 'SDIA 10H'),
        ('24', 'SDIA 24H'),
        ('42', 'LMKD'),
        ('48', 'DDIA 48H'),
        ('71', 'SABADOS')
    ]

    DELIVERY_INSTRUCTIONS = [
        ('0', 'Ninguna'),
        ('2', 'Devolver albarán firmado'),
        ('3', 'Acuse de recibo'),
        ('4', 'Retornar mercancía'),
        ('16', 'Envío con retorno')
    ]

    delivery_type = fields.Selection(selection_add=[('autoradio', 'AUTORADIO')])
    autoradio_service_code = fields.Selection(AUTORADIO_SERVICES)
    autoradio_delivery_instructions = fields.Selection(DELIVERY_INSTRUCTIONS)
    autoradio_config_id = fields.Many2one('autoradio.config', string='AUTORADIO Config')