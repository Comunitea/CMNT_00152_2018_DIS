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
from odoo import http, _
from odoo.http import request
from datetime import datetime, timedelta
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
            timestamp = params.get('timestamp', False) or datetime.now().timestamp()

            _logger.info(("Tratando de acceder a la API con timestamp: {}.").format(datetime.strptime(timestamp, '%Y%m%d%H%M%S')))

            log_entry = request.env['api.access.log'].sudo().create({
                'access_type': "send",
                'timestamp': timestamp,
                'token': token,
                'order_id': _id,
                'error': False
            })

            if timedelta(minutes=5) < datetime.now() - datetime.strptime(timestamp, '%Y%m%d%H%M%S'):
                _logger.error(
                    _("REST API called with a timestamp older than 5 minutes.")
                )
                
                log_entry.sudo().write({
                    'error': True,
                    'error_msg': _("REST API called with a timestamp older than 5 minutes.")
                })

                raise BadRequest(_("REST API called with a timestamp older than 5 minutes."))
            
            if not params or not token or not timestamp:

                _logger.error(
                    _("REST API called with no credentials")
                )
                log_entry.sudo().update({
                    'error': True,
                    'error_msg': _("REST API called with no credentials")
                })
                raise BadRequest(_("REST API called with no credentials"))
            else:
                self._api_check_access(_id, log_entry)
                self._api_authentication(token, timestamp, log_entry)

        return super(BaseRestUVigoApiController, self)._process_method(service_name, method_name, _id, params)

    def _api_authentication(self, token, timestamp, log_entry):
        
        api_key = request.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_key', False)
        api_string = request.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_string', False)
        api_partner = request.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_partner', False)

        if not api_key or not api_string or not api_partner:
            _logger.error(
                _("REST API values not configured.")
            )
            log_entry.sudo().update({
                'error': True,
                'error_msg': _("REST API values not configured.")
            })
            raise BadRequest(_("REST API values not configured."))

        self_token = "{}{}{}".format(api_string, timestamp, api_key)
        self_token_md5 = hashlib.md5(self_token.encode('utf-8')).hexdigest()
        if self_token_md5 == token:
            return True
        else:
            _logger.error(
                _("REST API called with a invalid token.")
            )
            log_entry.sudo().update({
                'error': True,
                'error_msg': _("REST API called with a invalid token.")
            })
            raise BadRequest(_("REST API called with a invalid token."))

    def _api_check_access(self, _id, log_entry):
        api_partner = request.env['ir.config_parameter'].sudo().get_param('rest_api_dismac.api_partner', False)
        if not _id:
            _logger.error(
                _("REST API called without order id.")
            )
            log_entry.sudo().update({
                'error': True,
                'error_msg': _("REST API called without order id.")
            })
            raise BadRequest(_("REST API called without order id."))

        sale_order = request.env['sale.order'].sudo().search([('id', '=', _id)])

        if not sale_order:
            _logger.error(
                _("REST API could not find that order number.")
            )
            log_entry.sudo().update({
                'error': True,
                'error_msg': _("REST API could not find that order number.")
            })
            raise BadRequest(_("REST API could not find that order number."))

        api_partner_obj = request.env['res.partner'].browse(int(api_partner))
        
        if not (api_partner_obj == sale_order.partner_id or api_partner_obj == sale_order.partner_id.parent_id):
            _logger.error(
                _("REST API access not allowed to this order.")
            )
            log_entry.sudo().update({
                'error': True,
                'error_msg': _("REST API access not allowed to this order.")
            })
            raise BadRequest(_("REST API access not allowed to this order."))
            
        return True