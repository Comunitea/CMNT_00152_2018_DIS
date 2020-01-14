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
{
    "name": "Rest Api Dismac",
    'version': '12.0.0.0.0',
    "summary": "Rest Api for Dismac based on OCA's rest-framework module",
    'description': '',
    'category': 'Custom',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    "license": "LGPL-3",
    'contributors': [
        'Vicente Ángel Gutiérrez Fernández <vicente@comunitea.com>',
    ],
    "depends": ["base_rest", "component", "sale", "website", "l10n_es_facturae"],
    "data": [
        'views/res_config.xml',
        'views/sale_order.xml',
        'views/api_access_log.xml',
        'security/ir.model.access.csv',
        'wizard/sale_order_wzd.xml'
    ],
    "demo": [],
    'images': [
        '/static/description/icon.png',
    ],
    'installable': True,
    'application': False,
}