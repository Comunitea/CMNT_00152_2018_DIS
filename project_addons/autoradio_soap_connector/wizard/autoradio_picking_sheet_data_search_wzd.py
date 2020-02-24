# -*- coding: utf-8 -*-
#
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#
##############################################################################
#
#    Copyright (C) 2020 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
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
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError

import datetime

_logger = logging.getLogger(__name__)

class AutoradioPickingSheetDataWizard(models.TransientModel):

    _name = "autoradio.picking.sheet.data.search.wzd"

    @api.model
    def _default_date(self):
        return fields.Datetime.now()

    @api.model
    def _get_default_center_code(self):
        config = self.env['autoradio.config'].search([('soap_url', '!=', None)])
        return config.soap_center

    @api.model
    def _get_default_client_code(self):
        config = self.env['autoradio.config'].search([('soap_url', '!=', None)])
        return config.soap_client_code

    client_code = fields.Integer(string="Client code", default=_get_default_client_code)
    center_code = fields.Integer(string="Center code", default=_get_default_center_code)
    date = fields.Datetime(string="Date", default=_default_date)

    def autoradio_picking_sheet_data_search(self):
        if not self.date:
            raise ValidationError(_("You need to send a date."))
        if not self.client_code:
            raise ValidationError(_("You need to send a client code."))
        if not self.center_code:
            self.env['autoradio.config'].WSObtenerDatosHojaRecogida(client_code=self.client_code, date=self.date.strftime('%d/%m/%Y'))
        else:
            self.env['autoradio.config'].WSObtenerDatosHojaRecogidaCentro(center_code=self.center_code, client_code=self.client_code, date=self.date.strftime('%d/%m/%Y'))