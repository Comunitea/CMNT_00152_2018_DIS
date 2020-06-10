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
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken
from datetime import datetime
from lxml import etree
import base64
import urllib.request
import ssl
from requests import Session
from requests.auth import HTTPBasicAuth

from odoo.exceptions import ValidationError, UserError, AccessError

from datetime import datetime, timedelta
import pytz

import logging.config

delivery_states = [
    ('not_sent', _('Not sent')),
    ('requested', _('Requested')),
    ('pending', _('Pending')),
    ('in_transition', _('In transition')),
    ('delivered', _('Delivered')),
    ('canceled', _('Canceled'))
]

class StockPicking(models.Model):

    _name = 'autoradio.picking.delivery'
    _description = "Autoradio picking delivery"
    _order = "id desc"

    @api.model
    def _default_delivery_date(self):
        return fields.Datetime.now()

    @api.multi
    def _compute_partner_id(self):
        for delivery in self:
            partner = delivery.picking_ids.mapped('partner_id')
            if len(partner) > 1:
                raise ValidationError(_("You can not add pickings from more than one partner."))
            delivery.partner_id = len(partner) == 1 and partner or False

    @api.multi
    def _compute_carrier_id(self):
        for delivery in self:
            for pick in delivery.picking_ids:
                pick.carrier_id = self.carrier_id
                pick.carrier_tracking_ref = self.carrier_tracking_ref

    @api.multi
    @api.depends('picking_ids')
    def _compute_autoradio_picking_reference(self):
        for delivery in self:
            picking_reference = ""
            for pick in delivery.picking_ids:
                picking_reference += "{} ".format(pick.name)
            delivery.autoradio_picking_reference = picking_reference
                
    # Pickings info
    name = fields.Char('Name', required=True, index=True, copy=False, unique=True,
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'autoradio.picking.delivery'
        ),
    )
    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        string='Pickings',
        inverse_name='autoradio_picking_delivery_id'
    )
    autoradio_picking_reference = fields.Char(string="Reference", compute="_compute_autoradio_picking_reference")
    shipping_weight = fields.Float(string='Shipping Weight')
    number_of_packages = fields.Integer(string='Number of packages')
    carrier_tracking_ref = fields.Char(string='Carrier Tracking Ref')
    delivery_date = fields.Datetime(string="Date from", default=_default_delivery_date)
    carrier_id = fields.Many2one(comodel_name='delivery.carrier', string='Carrier', domain=[('delivery_type', '=', 'autoradio')])
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', readonly=True, compute="_compute_partner_id")
    state = fields.Selection(delivery_states, string="Delivery Status", default="not_sent")

    # Autoradio config INFO
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
    autoradio_send_today = fields.Boolean(string="Send today", default=True)
    autoradio_close_shipping = fields.Boolean(string="Close shipping", default=False)
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
    autoradio_signed_picking = fields.Boolean(string="Return Signed", default=False)
    autoradio_acknowledgement_receipt = fields.Boolean(string="Acknowledgement of receipt", default=True)
    autoradio_return_goods = fields.Boolean(string="Return Goods", default=False)
    autoradio_delivery_with_return = fields.Boolean(string="Delivery with Return", default=False)
    autoradio_delivery_instructions = fields.Integer(readonly=True, compute="_compute_delivery_instructions")
    
    #WSGrabarEnvioTAR
    autoradio_ccbb = fields.Char(string='Barcode')
    autoradio_ccbb_type = fields.Selection([
        (1, 'Code128'),
        (2, 'Interleaved 2of5')
        ], string='Barcode Type')
    autoradio_channelling = fields.Char(string='Channelling')

    @api.onchange('autoradio_signed_picking', 'autoradio_acknowledgement_receipt', 
    'autoradio_return_goods', 'autoradio_delivery_with_return')
    def _compute_delivery_instructions(self):
        self.autoradio_delivery_instructions = 0
        if self.autoradio_signed_picking:
            self.autoradio_delivery_instructions += 2
        #Opciones no están disponibles en la api
        #if self.autoradio_acknowledgement_receipt:
        #    self.autoradio_delivery_instructions += 3 # 4 en la documentación oficial
        #if self.autoradio_return_goods:
        #    self.autoradio_delivery_instructions += 4 # 8 en la documentación oficial
        if self.autoradio_delivery_with_return:
            self.autoradio_delivery_instructions += 4 # 16 en la documentación

    @api.onchange('picking_ids')
    def onchange_picking_ids(self):
        self._compute_partner_id()
        self.shipping_weight = 0.0
        for pack in self.picking_ids:
            pack.carrier_id = self.carrier_id
            if pack.shipping_weight != 0.0:
                self.shipping_weight += pack.shipping_weight
            else:
                self.shipping_weight += pack.weight_bulk

        self.number_of_packages = sum(self.picking_ids.mapped('number_of_packages'))

    @api.multi
    def send_autoradio_picking_tar(self):
        for delivery in self:
            if not delivery.carrier_tracking_ref:
                delivery.WSGrabarEnvioTAR()
            else:
                delivery.WSEditarEnvioTAR()

    @api.multi
    def delete_autoradio_shipping(self):
        for delivery in self:
            if delivery.carrier_tracking_ref:
                delivery.WSBorrarEnvio()

    #@api.multi
    #def get_label_from_autoradio(self):
    #    for delivery in self:
    #        if delivery.carrier_tracking_ref:
    #            tag_data = delivery.WSObtenerDatosEtiqueta()
    #            print(tag_data)
    #            if tag_data:
    #                return self.env.ref('autoradio_soap_connector.autoradio_label_report').with_context(data=tag_data)
                    

    @api.multi
    def get_barcode_from_autoradio(self):
        for delivery in self:
            if delivery.carrier_tracking_ref:
                delivery.WSObtenerCCBB()

    def WSGrabarEnvioTAR(self):
        if not self:
            raise UserError(_("You need to select a picking to calculate the estimated shipping cost."))

        config = self.env['autoradio.config'].search([('soap_url', '!=', None)])
        config = self.env['autoradio.config'].browse(config.id)

        client, history = config.create_client()
        if client:
            try:
                header = config.getWSRequestHeader(client)

                grabarEnvioTAR = {
                    'LoginCliente': config.soap_persona_ordena,
                    'CodCliente': config.soap_client_code,
                    'CodCentro': config.soap_center,
                    'Fecha': self.delivery_date.strftime('%Y/%m/%d %H:%M'),
                    'CodServicio': self.carrier_id.autoradio_service_code,
                    # Sender
                    'Remitente': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.name,
                    'CifRemi': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.vat,
                    'DireccionRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **"{}, {}".format(self.company_id.street, self.company_id.street2),
                    'PoblacionRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.city,
                    'CodPosRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.zip.zfill(5),
                    'CodPosPorRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **000,
                    'PaisRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **'ESP' if self.company_id.country_id.code == 'ES' else 'POR' if self.company_id.country_id.code == 'PT' else False,
                    'MailRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.email or '',
                    'TlfRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.phone or '',
                    'MovilRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **'',
                    # Recipient
                    'Destinatario': self.partner_id.name,
                    'CifDes': self.partner_id.vat or '',
                    'DireccionDes': "{}, {}".format(self.partner_id.street or '', self.partner_id.street2 or ''),
                    'PoblacionDes': self.partner_id.city,
                    'CodPosDes': self.partner_id.zip.zfill(5) if self.partner_id.country_id.code == 'ES' else self.partner_id.zip.split("-")[0].zfill(0) if self.partner_id.country_id.code == 'PT' else False,
                    'CodPosPorDes': '000' if self.partner_id.country_id.code == 'ES' else self.partner_id.zip.split("-")[1].zfill(0) if self.partner_id.country_id.code == 'PT' else False,
                    'PaisDes': 'ESP' if self.partner_id.country_id.code == 'ES' else 'POR' if self.partner_id.country_id.code == 'PT' else False,
                    'MailDes': self.partner_id.email or '',
                    'TlfDes': self.partner_id.phone or '',
                    'MovilDes': self.partner_id.mobile or '',
                    'ContactoDes': self.partner_id.name,
                    # Other data
                    'Bultos': self.number_of_packages,
                    'Kilos': self.shipping_weight,
                    'TipoPorte': self.autoradio_type, # P for paid, D for debt
                    'Reembolso': self.autoradio_refund_amount, # Amount in EUR
                    'TipoComision': self.autoradio_refund_type, # P for paid, D for debt
                    'Obser': self.autoradio_obs if self.autoradio_obs else '', # Comments
                    'AmpliaObser': self.autoradio_obs_extra if self.autoradio_obs_extra else '',
                    'RefCliente': self.autoradio_picking_reference, # ref client - changed from picking.partner_id.ref 
                    'InstOp': self.autoradio_delivery_instructions,
                    'PersonaOrdena': config.soap_persona_ordena,
                    'FlagEnviarHoy': 1 if self.autoradio_close_shipping or self.autoradio_send_today else 0, # send today = 1.
                    'Cierre': 1 if self.autoradio_close_shipping else 0, # 0 or 1. Cerrar envío.
                    'FormaCobroReembolso': self.autoradio_cash_on_delivery_payment if self.autoradio_cash_on_delivery_payment else 9, # 9 - Efectivo, 10 - Cheque/Pagaré, 11 - Cheque a la vista, 12- Indiferente.
                    'Cheque1': self.autoradio_check_1_amount if self.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha1': self.autoradio_check_1_date.strftime('%Y/%m/%d %H:%M') if self.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque2': self.autoradio_check_2_amount if self.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha2': self.autoradio_check_2_date.strftime('%Y/%m/%d %H:%M') if self.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque3': self.autoradio_check_3_amount if self.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha3': self.autoradio_check_3_date.strftime('%Y/%m/%d %H:%M') if self.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque4': self.autoradio_check_4_amount if self.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha4': self.autoradio_check_4_date.strftime('%Y/%m/%d %H:%M') if self.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Desembolso': self.autoradio_payment, # Importe de los portes?
                    'Referencia': self.name
                }
            
                res = client.service.WSGrabarEnvioTAR(**grabarEnvioTAR, _soapheaders=[header])

                if res:
                    self.update({
                        'carrier_tracking_ref': res[1],
                        'autoradio_ccbb': res[2],
                        'autoradio_channelling': res[3],
                        'autoradio_ccbb_type': res[4],
                        'state': 'requested'
                    })
                    self._compute_carrier_id()
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def WSEditarEnvioTAR(self):
        if not self:
            raise UserError(_("You need to select a picking to calculate the estimated shipping cost."))

        config = self.env['autoradio.config'].search([('soap_url', '!=', None)])
        config = self.env['autoradio.config'].browse(config.id)

        client, history = config.create_client()
        if client:
            try:
                header = config.getWSRequestHeader(client)

                editarEnvioTAR = {
                    'RefEnvio': self.carrier_tracking_ref,
                    'LoginCliente': config.soap_persona_ordena,
                    'CodCliente': config.soap_client_code,
                    'CodCentro': config.soap_center,
                    'Fecha': self.delivery_date.strftime('%Y/%m/%d %H:%M'),
                    'CodServicio': self.carrier_id.autoradio_service_code,
                    # Sender
                    'Remitente': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.name,
                    'CifRemi': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.vat,
                    'DireccionRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **"{}, {}".format(self.company_id.street, self.company_id.street2),
                    'PoblacionRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.city,
                    'CodPosRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.zip.zfill(5),
                    'CodPosPorRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **000,
                    'PaisRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **'ESP' if self.company_id.country_id.code == 'ES' else 'POR' if self.company_id.country_id.code == 'PT' else False,
                    'MailRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.email or '',
                    'TlfRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **self.company_id.phone or '',
                    'MovilRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **'',
                    # Recipient
                    'Destinatario': self.partner_id.name,
                    'CifDes': self.partner_id.vat or '',
                    'DireccionDes': "{}, {}".format(self.partner_id.street or '', self.partner_id.street2 or ''),
                    'PoblacionDes': self.partner_id.city,
                    'CodPosDes': self.partner_id.zip.zfill(5) if self.partner_id.country_id.code == 'ES' else self.partner_id.zip.split("-")[0].zfill(0) if self.partner_id.country_id.code == 'PT' else False,
                    'CodPosPorDes': '000' if self.partner_id.country_id.code == 'ES' else self.partner_id.zip.split("-")[1].zfill(0) if self.partner_id.country_id.code == 'PT' else False,
                    'PaisDes': 'ESP' if self.partner_id.country_id.code == 'ES' else 'POR' if self.partner_id.country_id.code == 'PT' else False,
                    'MailDes': self.partner_id.email or '',
                    'TlfDes': self.partner_id.phone or '',
                    'MovilDes': self.partner_id.mobile or '',
                    'ContactoDes': self.partner_id.name,
                    # Other data
                    'Bultos': self.number_of_packages,
                    'Kilos': self.shipping_weight,
                    'TipoPorte': self.autoradio_type, # P for paid, D for debt
                    'Reembolso': self.autoradio_refund_amount, # Amount in EUR
                    'TipoComision': self.autoradio_refund_type, # P for paid, D for debt
                    'Obser': self.autoradio_obs if self.autoradio_obs else '', # Comments
                    'AmpliaObser': self.autoradio_obs_extra if self.autoradio_obs_extra else '',
                    'RefCliente': self.autoradio_picking_reference, # ref client - changed from picking.partner_id.ref 
                    'InstOp': self.autoradio_delivery_instructions,
                    'PersonaOrdena': config.soap_persona_ordena,
                    'FlagEnviarHoy': 1 if self.autoradio_close_shipping or self.autoradio_send_today else 0, # send today = 1.
                    'Cierre': 1 if self.autoradio_close_shipping else 0, # 0 or 1. Cerrar envío.
                    'FormaCobroReembolso': self.autoradio_cash_on_delivery_payment if self.autoradio_cash_on_delivery_payment else 9, # 9 - Efectivo, 10 - Cheque/Pagaré, 11 - Cheque a la vista, 12- Indiferente.
                    'Cheque1': self.autoradio_check_1_amount if self.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha1': self.autoradio_check_1_date.strftime('%Y/%m/%d %H:%M') if self.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque2': self.autoradio_check_2_amount if self.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha2': self.autoradio_check_2_date.strftime('%Y/%m/%d %H:%M') if self.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque3': self.autoradio_check_3_amount if self.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha3': self.autoradio_check_3_date.strftime('%Y/%m/%d %H:%M') if self.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque4': self.autoradio_check_4_amount if self.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha4': self.autoradio_check_4_date.strftime('%Y/%m/%d %H:%M') if self.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Desembolso': self.autoradio_payment, # Importe de los portes?
                    'Referencia': self.name
                }
            
                res = client.service.WSEditarEnvioTAR(**editarEnvioTAR, _soapheaders=[header])

                if res:
                    self.update({
                        'autoradio_ccbb': res[1],
                        'autoradio_channelling': res[2],
                        'autoradio_ccbb_type': res[3],
                        'state': 'requested'
                    })
                    self._compute_carrier_id()
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))
    
    def WSBorrarEnvio(self):
        if not self:
            raise UserError(_("You need to select a picking to calculate the estimated shipping cost."))

        config = self.env['autoradio.config'].search([('soap_url', '!=', None)])
        config = self.env['autoradio.config'].browse(config.id)

        client, history = config.create_client()
        if client:
            try:
                header = config.getWSRequestHeader(client)

                borrarEnvio = {
                    'RefEnvio': self.carrier_tracking_ref,
                    'LoginCliente': config.soap_persona_ordena,
                    'CodCliente': config.soap_client_code,
                    'CodCentro': config.soap_center
                }
            
                res = client.service.WSBorrarEnvio(**borrarEnvio, _soapheaders=[header])

                if res and res[0] == 1:
                    self.update({
                        'carrier_tracking_ref': False,
                        'autoradio_ccbb': False,
                        'autoradio_channelling': False,
                        'autoradio_ccbb_type': False,
                        'state': 'not_sent'
                    })
                    self._compute_carrier_id()
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def WSObtenerDatosEtiqueta(self):
        if not self:
            raise UserError(_("You need to select a picking to calculate the estimated shipping cost."))

        config = self.env['autoradio.config'].search([('soap_url', '!=', None)])
        config = self.env['autoradio.config'].browse(config.id)

        client, history = config.create_client()
        if client:
            try:
                header = config.getWSRequestHeader(client)

                obtenerDatosEtiqueta = {
                    'LoginCliente': config.soap_persona_ordena,
                    'RefEnvio': self.carrier_tracking_ref
                }
            
                res = client.service.WSObtenerDatosEtiqueta(**obtenerDatosEtiqueta, _soapheaders=[header])

                if res:
                    if history.last_received["envelope"][0][0][0] is not None:
                        response = history.last_received["envelope"][0][0][0]
                    else:
                        raise AccessError(_("No existen datos para este envío."))
                    
                    response_content = etree.tostring(response, encoding="unicode", pretty_print=True)
                    root = etree.fromstring(response_content)
                    datosEtiqueta = root.findall('.//datosEtiqueta')
                    if not datosEtiqueta:
                        raise AccessError(_("No existen datos para este envío."))
                    tag_dict = self.elem2dict(datosEtiqueta[0])
                    return tag_dict
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))
    
    def WSObtenerCCBB(self):
        if not self:
            raise UserError(_("You need to select a picking to calculate the estimated shipping cost."))

        config = self.env['autoradio.config'].search([('soap_url', '!=', None)])
        config = self.env['autoradio.config'].browse(config.id)

        client, history = config.create_client()
        if client:
            try:
                header = config.getWSRequestHeader(client)

                obtenerCCBB = {
                    'LoginCliente': config.soap_persona_ordena,
                    'RefEnvio': self.carrier_tracking_ref
                }
            
                res = client.service.WSObtenerCCBB(**obtenerCCBB, _soapheaders=[header])

                if res:
                    print("{}".format(res))
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def elem2dict(self, node):
        """
        Convert an lxml.etree node tree into a dict.
        """
        result = {}

        for element in node.iterchildren():
            # Remove namespace prefix
            key = element.tag.split('}')[1] if '}' in element.tag else element.tag

            # Process element as tree element if the inner XML contains non-whitespace content
            if element.text and element.text.strip():
                value = element.text
            else:
                value = self.elem2dict(element)
            if key in result:

                
                if type(result[key]) is list:
                    result[key].append(value)
                else:
                    tempvalue = result[key].copy()
                    result[key] = [tempvalue, value]
            else:
                result[key] = value
        return result