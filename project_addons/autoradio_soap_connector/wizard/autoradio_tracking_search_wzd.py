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
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError

import datetime

_logger = logging.getLogger(__name__)

class AutoradioTrackingWizard(models.TransientModel):

    _name = "autoradio.tracking.search.wzd"

    @api.model
    def _default_start(self):
        return fields.Datetime.now()

    @api.model
    def _default_end(self):
        return self._default_start() + datetime.timedelta(days=30, hours=8)

    @api.model
    def _get_default_center_code(self):
        config = self.env['autoradio.config'].search([('soap_url', '!=', None)])
        return config.soap_center

    s_type = fields.Selection([
        ('E', _('Shipping')),
        ('R', _('Picking'))
        ], string='Search type', default="E")
    center_code = fields.Integer(string="Center code", default=_get_default_center_code)
    reference = fields.Char(string="Reference")
    dates = fields.Boolean(string="Search between dates", default=False)
    date_from = fields.Datetime(string="Date from", default=_default_start)
    date_to = fields.Datetime(string="Date to", default=_default_end)

    def autoradio_tracking_search(self):
        if not self.s_type:
            raise ValidationError(_("You need to select a search type."))
        if not self.dates:
            self.env['autoradio.config'].WSBuscadorTracking(codigoCentro=self.center_code, reference=self.reference, tipo=self.s_type)
        elif self.dates and self.date_from and self.date_to:
            self.env['autoradio.config'].WSBuscadorTrackingEntreFechas(date_from=self.date_from.strftime('%Y-%m-%dT%H:%M:%S'), date_to=self.date_to.strftime('%Y-%m-%dT%H:%M:%S'), tipo=self.s_type)
        else:
            raise ValidationError(_("You need to select the dates."))