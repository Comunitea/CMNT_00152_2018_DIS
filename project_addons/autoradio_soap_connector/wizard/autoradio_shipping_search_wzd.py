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

class AutoradioSearchWizard(models.TransientModel):

    _name = "autoradio.shipping.search.wzd"

    @api.model
    def _get_current_year(self):
        return datetime.datetime.strptime(datetime.datetime.now().strftime('%Y'), '%Y').strftime('%Y')

    s_type = fields.Selection([
        ('shipping', _('Shipping')),
        ('picking', _('Picking'))
        ], string='Search type', default="shipping")
    year = fields.Integer(string="Shipping year", default=_get_current_year)
    reference = fields.Char(string="Shipping reference")
    r_type = fields.Selection([
        ('0', _('Autoradio Ref.')),
        ('1', _('Own Ref.'))
        ], string='Reference type')

    def autoradio_shipping_search(self):
        if self.s_type == 'shipping':
            self.env['autoradio.config'].WSBuscadorEnvio(year=self.year, numeroExpedicion=self.reference, tipo=self.r_type)
        elif self.s_type == 'picking':
            self.env['autoradio.config'].WSBuscadorRecogida(year=self.year, numeroExpedicion=self.reference, tipo=self.r_type)
        else:
            raise ValidationError(_("You need to select a search type."))