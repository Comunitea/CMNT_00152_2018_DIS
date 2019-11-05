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

from odoo.addons.base_rest.controllers import main
from werkzeug.exceptions import BadRequest
from odoo import http
from odoo.http import request
from datetime import datetime
import hashlib
import logging

_logger = logging.getLogger(__name__)

class BaseRestUVigoApiController(main.RestController):
    _root_path = "/uvigo/"
    _collection_name = "base.rest.uvigo.services"
    _default_auth = "public"

    def _process_method(self, service_name, method_name, _id=None, params=None):
        if service_name == 'pedidos' or service_name == 'sale.order':
            service_name = 'sale.order'
            token = params.get('token', False)
            timestamp = params.get('timestamp', False)
            if not params or not token or not timestamp:

                _logger.error(
                    "REST API called with no credentials"
                )
                raise BadRequest("REST API called with no credentials")
            else:
                self._api_authentication(token, timestamp)

        return super(BaseRestUVigoApiController, self)._process_method(service_name, method_name, _id, params)

    def _api_authentication(self, token, timestamp):
        #token = "{}{}{}".format("uvigo", datetime.now().strftime("%Y%m%d%H%M%S"), api_key)
        api_key = request.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_key', False)
        api_string = request.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_string', False)

        if not api_key or not api_string:
            _logger.error(
                "REST API values not configured."
            )
            raise BadRequest("REST API values not configured.")

        self_token = "{}{}{}".format(api_string, timestamp, api_key)
        self_token_md5 = hashlib.md5(self_token.encode('utf-8')).hexdigest()
        if self_token_md5 == token:
            return True
        else:
            _logger.error(
                "REST API called with a invalid token."
            )
            raise BadRequest("REST API called with a invalid token.")