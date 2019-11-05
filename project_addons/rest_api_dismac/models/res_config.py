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

from odoo import fields, models, api, _

API_PARAMS = ['api_key', 'api_string']

class ConfigAPIData(models.TransientModel):

    _inherit = 'res.config.settings'

    api_key = fields.Char('API KEY', help="API KEY for token authentication")
    api_string = fields.Char('API String', help="API String for token authentication")

    @api.model
    def get_values(self):
        ICP =self.env['ir.config_parameter'].sudo()
        res = super(ConfigAPIData, self).get_values()
        for param in API_PARAMS:
            value= ICP.get_param('rest_api_dismac.{}'.format(param), False)
            res.update({param: value})
        return res

    @api.multi
    def set_values(self):
        super(ConfigAPIData, self).set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        for param in API_PARAMS:
            ICP.set_param('rest_api_dismac.{}'.format(param), self[param])