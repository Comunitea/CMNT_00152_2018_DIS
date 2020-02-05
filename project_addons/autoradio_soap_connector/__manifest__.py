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
{
    'name': 'autoradio soap connector',
    'version': '12.0.0.0.0',
    'summary': 'SOAP website integration with Autoradio',
    'category': 'Custom',
    'author': 'comunitea',
    'website': 'www.comunitea.com',
    'license': 'AGPL-3',
    'depends': [
        "delivery",
        "stock",
        "base_delivery_carrier_label",
        "base_report_to_printer",
        'queue_job'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/autoradio_config.xml',
        'views/delivery_views.xml',
        'views/stock_picking.xml',
        'wizard/autoradio_shipping_search_wzd.xml',
        'wizard/autoradio_tracking_search_wzd.xml', 
        'wizard/autoradio_delivery_agreement_search_wzd.xml',
        'wizard/autoradio_picking_sheet_data_search_wzd.xml'
    ],
    "external_dependencies": {
        "python": [
            "zeep"
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
