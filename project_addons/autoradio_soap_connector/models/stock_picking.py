# -*- coding: utf-8 -*-
##############################################################################
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    Copyright (C) 2020 Comunitea Servicios Tecnológicos S.L. All Rights Reserved
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

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    #INFO
    autoradio_type = fields.Selection([
        ('P', _('Paid')),
        ('D', _('Debt'))
    ], string="Shipping Charge", default="P")
    autoradio_refund_amount = fields.Float(string="Refund amount", help="Refund amount allows to calculate the commission", default=0.0)
    autoradio_refund_type = fields.Selection([
        ('P', _('Paid')),
        ('D', _('Debt'))
    ], string="Refund Type", default="P")
    autoradio_obs = fields.Char(string="Info about the shipping")
    autoradio_obs_extra = fields.Char(string="Extra info about the shipping")
    autoradio_send_today = fields.Boolean(string="Send today")
    autoradio_close_shipping = fields.Boolean(string="Close shipping")
    autoradio_cash_on_delivery_payment = fields.Selection([
        (9, _('Cash')),
        (10, _('Check/Promissory Note')),
        (11, _('Bearer Check')),
        (12, _('Any')),
    ], string="Cash on delivery payment", default=9)
    autoradio_check_1_amount = fields.Float(string="Amount of the 1st payment", default=0.0)
    autoradio_check_1_date = fields.Datetime(string="Date of the 1st payment")
    autoradio_check_2_amount = fields.Float(string="Amount of the 2nd payment", default=0.0)
    autoradio_check_2_date = fields.Datetime(string="Date of the 2nd payment")
    autoradio_check_3_amount = fields.Float(string="Amount of the 3rd payment", default=0.0)
    autoradio_check_3_date = fields.Datetime(string="Date of the 3rd payment")
    autoradio_check_4_amount = fields.Float(string="Amount of the 4th payment", default=0.0)
    autoradio_check_4_date = fields.Datetime(string="Date of the 4th payment")
    autoradio_payment = fields.Float(string="Payment", default=0.0)
    autoradio_declared_value = fields.Float(string="Declared Value", default=0.0)
    autoradio_hard_to_handle = fields.Boolean(string="Hard to handle", help="Hard to handle merchandise.", default=0)
    #WSCalculoTarifa
    autoradio_estimated_price_rate = fields.Char(string='Autoradio Estimated Prices')
    #WSGrabarEnvioTAR
    autoradio_expedition_number = fields.Char(string='Autoradio Expedition Number')
    autoradio_ccbb = fields.Char(string='Barcode')
    autoradio_ccbb_type = fields.Selection([
        ('1', 'Code128'),
        ('2', 'Interleaved 2of5')
        ], string='Barcode Type')
    autoradio_channelling = fields.Char(string='Channelling')
    

    @api.multi
    def get_estimated_price_rate_from_autoradio(self):
        for picking in self:
            self.env['autoradio.config'].WSCalculoTarifa(picking)

    @api.multi
    def send_autoradio_picking_tar(self):
        for picking in self:
            if not picking.autoradio_expedition_number:
                self.env['autoradio.config'].WSGrabarEnvioTAR(picking)
            else:
                self.env['autoradio.config'].WSEditarEnvioTAR(picking)

    @api.multi
    def add_autoradio_package(self):
        for picking in self:
            self.env['autoradio.config'].WSAgregarBulto(picking)

    @api.multi
    def delete_autoradio_shipping(self):
        for picking in self:
            if picking.autoradio_expedition_number:
                self.env['autoradio.config'].WSBorrarEnvio(picking)

    @api.multi
    def get_barcode_from_autoradio(self):
        for picking in self:
            if picking.autoradio_expedition_number:
                self.env['autoradio.config'].WSObtenerCCBB(picking)

    @api.multi
    def get_label_from_autoradio(self):
        for picking in self:
            if picking.autoradio_expedition_number:
                self.env['autoradio.config'].WSObtenerDatosEtiqueta(picking)