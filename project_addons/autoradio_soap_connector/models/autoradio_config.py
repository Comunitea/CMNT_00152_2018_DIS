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
from zeep.plugins import HistoryPlugin
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

#logging.config.dictConfig({
#    'version': 1,
#    'formatters': {
#        'verbose': {
#            'format': '%(name)s: %(message)s'
#        }
#    },
#    'handlers': {
#        'console': {
#            'level': 'DEBUG',
#           'class': 'logging.StreamHandler',
#            'formatter': 'verbose',
#        },
#    },
#    'loggers': {
#        'zeep.transports': {
#            'level': 'DEBUG',
#            'propagate': True,
#            'handlers': ['console'],
#       },
#   }
#})



class ConfigAutoradio(models.Model):

    _name = 'autoradio.config'

    soap_url = fields.Char(default="https://clientes.tautoradio.com:49179/Autoradio.asmx?wsdl", string='Webservice URL')
    soap_user = fields.Char('SOAP User')
    soap_pass = fields.Char('SOAP password')
    soap_client_code = fields.Integer('SOAP Client Code')
    soap_center = fields.Integer('SOAP Center Code')
    soap_persona_ordena = fields.Char('SOAP Persona Ordena')

    def getWSRequestHeader(self, client):
        try:
            element_type = client.get_element("{http://clientes.tautoradio.com}WSRequestHeader")
            WSRequestHeader = element_type(
                login=self.soap_user,
                password=self.soap_pass
            )
            return WSRequestHeader
        except Exception as e:
            print("Error: {}".format(e))
            return False

    def create_client(self):
        session = Session()
        session.verify = False       

        try:
            transport = Transport(cache=SqliteCache(), session=session)
            history = HistoryPlugin()
            client = Client(self.soap_url, transport=transport, plugins=[history])

            if client:
                print("client: {}".format(client))
                return client, history
            else:
                raise AccessError(_("Not possible to establish a client."))
        except Exception as e:
            raise AccessError(_("Access error message: {}".format(e)))


    def WSBuscadorEnvio(self, year=False, numeroExpedicion=False, tipo=False):
        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)
                
                tz = pytz.timezone(self.env.user.tz if self.env.user.tz else 'Europe/Madrid')
                current_year = datetime.now().astimezone(tz).strftime('%Y')

                buscadorEnvio = {
                    'loginCliente': self.soap_persona_ordena,
                    'codigoCliente': self.soap_client_code,
                    'codigoCentro': self.soap_center,
                    'ano': year if year else int(current_year),
                    'numeroExpedicion': numeroExpedicion if numeroExpedicion else False,
                    'tipo': tipo if tipo else 0
                }
            
                res = client.service.WSBuscadorEnvio(**buscadorEnvio, _soapheaders=[header])

                print(res)
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def WSBuscadorRecogida(self, year=False, numeroExpedicion=False, tipo=False):
        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)
                
                tz = pytz.timezone(self.env.user.tz if self.env.user.tz else 'Europe/Madrid')
                current_year = datetime.now().astimezone(tz).strftime('%Y')

                buscadorRecogida = {
                    'loginCliente': self.soap_persona_ordena,
                    'codigoCliente': self.soap_client_code,
                    'codigoCentro': self.soap_center,
                    'ano': year if year else int(current_year),
                    'numRecogida': numeroExpedicion if numeroExpedicion else False,
                    'tipo': tipo if tipo else 0
                }
            
                res = client.service.WSBuscadorRecogida(**buscadorRecogida, _soapheaders=[header])
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def WSBuscadorTracking(self, tipo=False, codigoCentro=False, reference=False):
        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)

                buscadorTracking = {
                    'loginCliente': self.soap_persona_ordena,
                    'codigoCliente': self.soap_client_code,
                    'codigoCentroCliente': self.soap_center,
                    'codCentro': codigoCentro if codigoCentro else '',
                    'referencia': reference if reference else '',
                    'tipo': tipo if tipo else 'E'
                }
            
                res = client.service.WSBuscadorTracking(**buscadorTracking, _soapheaders=[header])
                print(res)
                #res_2 = etree.tostring(res['_value_1'], encoding="unicode", pretty_print=True)
                #print(res_2)
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def WSBuscadorTrackingEntreFechas(self, tipo=False, date_from=False, date_to=False):
        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)

                buscadorTrackingEntreFechas = {
                    'loginCliente': self.soap_persona_ordena,
                    'codigoCliente': self.soap_client_code,
                    'codigoCentroCliente': self.soap_center,
                    'tipo': tipo if tipo else 'E',
                    'fechaDesde': date_from if date_from else '',
                    'fechaHasta': date_to if date_to else '',                    
                }
            
                res = client.service.WSBuscadorTrackingEntreFechas(**buscadorTrackingEntreFechas, _soapheaders=[header])
                print(res)
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def WSBuscadorConformeEntrega(self, codigoCentro=False, reference=False):
        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)

                buscadorConformeEntrega = {
                    'loginCliente': self.soap_persona_ordena,
                    'codigoCliente': self.soap_client_code,
                    'codigoCentroCliente': self.soap_center,
                    'referencia': reference if reference else '',
                    'codCentro': codigoCentro if codigoCentro else ''
                }
            
                res = client.service.WSBuscadorConformeEntrega(**buscadorConformeEntrega, _soapheaders=[header])
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def WSBuscadorConformeEntregaEntreFechas(self, date_from=False, date_to=False):
        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)

                buscadorConformeEntregaEntreFechas = {
                    'loginCliente': self.soap_persona_ordena,
                    'codigoCliente': self.soap_client_code,
                    'codigoCentroCliente': self.soap_center,
                    'fechaDesde': date_from if date_from else '',
                    'fechaHasta': date_to if date_to else '', 
                }
            
                res = client.service.WSBuscadorConformeEntregaEntreFechas(**buscadorConformeEntregaEntreFechas, _soapheaders=[header])
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    #Deprecated
    def WSCalculoTarifa(self, picking=False):
        if not picking:
            raise UserError(_("You need to select a picking to calculate the estimated shipping cost."))

        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)

                calculoTarifa = {
                    'LoginCliente': self.soap_persona_ordena,
                    'CodCliente': self.soap_client_code,                  
                    'CodServicio': picking.carrier_id.autoradio_service_code,
                    # package data
                    'CodPosOri': picking.company_id.zip,
                    'CodPosDes': picking.partner_id.zip.zfill(5) if picking.partner_id.country_id.code == 'ES' else picking.partner_id.zip.split("-")[0].zfill(0) if picking.partner_id.country_id.code == 'PT' else False,
                    'PaisOri': 'ESP' if picking.company_id.country_id.code == 'ES' else 'POR' if picking.company_id.country_id.code == 'PT' else False,
                    'PaisDes': 'ESP' if picking.partner_id.country_id.code == 'ES' else 'POR' if picking.partner_id.country_id.code == 'PT' else False,
                    'Bultos': picking.number_of_packages,
                    'Peso': picking.shipping_weight,
                    'Alto': 0,
                    'Ancho': 0,
                    'Fondo': 0,
                    'ValorDeclarado': picking.autoradio_declared_value,
                    'Reembolso': picking.autoradio_refund_amount,
                    'MDM': 1 if picking.autoradio_hard_to_handle else 0, # Mercancía de difícil manipulación = 1.
                    'RAF': 1 if picking.carrier_id.autoradio_delivery_instructions in ['2'] else 0 # Devolver el albarán del cliente firmado = 1.
                }
            
                res = client.service.WSCalculoTarifa(**calculoTarifa, _soapheaders=[header])
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))
    
    #Sin uso ya que utilizamos autoradio.picking.delivery como gestor de envíos.
    def WSAgregarBulto(self, picking=False):
        if not picking:
            raise UserError(_("You need to select a picking to calculate the estimated shipping cost."))

        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)

                #cambiar por paquete
                agregarBulto = {
                    'LoginCliente': self.soap_persona_ordena,
                    'CodCliente': self.soap_client_code,
                    'CodCentro': self.soap_center,
                    'Fecha': picking.scheduled_date.strftime('%Y/%m/%d %H:%M'),
                    'CodServicio': picking.carrier_id.autoradio_service_code,
                    # Sender
                    'Remitente': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.name,
                    'CifRemi': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.vat,
                    'DireccionRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **"{}, {}".format(picking.company_id.street, picking.company_id.street2),
                    'PoblacionRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.city,
                    'CodPosRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.zip.zfill(5),
                    'CodPosPorRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **000,
                    'PaisRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **'ESP' if picking.company_id.country_id.code == 'ES' else 'POR' if picking.company_id.country_id.code == 'PT' else False,
                    'MailRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.email or '',
                    'TlfRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.phone or '',
                    'MovilRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **'',
                    # Recipient
                    'Destinatario': picking.partner_id.name,
                    'CifDes': picking.partner_id.vat or '',
                    'DireccionDes': "{}, {}".format(picking.partner_id.street or '', picking.partner_id.street2 or ''),
                    'PoblacionDes': picking.partner_id.city,
                    'CodPosDes': picking.partner_id.zip.zfill(5) if picking.partner_id.country_id.code == 'ES' else picking.partner_id.zip.split("-")[0].zfill(0) if picking.partner_id.country_id.code == 'PT' else False,
                    'CodPosPorDes': '000' if picking.partner_id.country_id.code == 'ES' else picking.partner_id.zip.split("-")[1].zfill(0) if picking.partner_id.country_id.code == 'PT' else False,
                    'PaisDes': 'ESP' if picking.partner_id.country_id.code == 'ES' else 'POR' if picking.partner_id.country_id.code == 'PT' else False,
                    'MailDes': picking.partner_id.email or '',
                    'TlfDes': picking.partner_id.phone or '',
                    'MovilDes': picking.partner_id.mobile or '',
                    'ContactoDes': picking.partner_id.name,
                    # Other data
                    'Bultos': picking.number_of_packages,
                    'Kilos': picking.shipping_weight,
                    'TipoPorte': picking.autoradio_type, # P for paid, D for debt
                    'Reembolso': picking.autoradio_refund_amount, # Amount in EUR
                    'TipoComision': picking.autoradio_refund_type, # P for paid, D for debt
                    'Obser': picking.autoradio_obs if picking.autoradio_obs else '', # Comments
                    'AmpliaObser': picking.autoradio_obs_extra if picking.autoradio_obs_extra else '',
                    'RefCliente': picking.partner_id.ref, # ref client
                    'InstOp': picking.carrier_id.autoradio_delivery_instructions,
                    'PersonaOrdena': self.soap_persona_ordena,
                    'FlagEnviarHoy': 1 if picking.autoradio_close_shipping or picking.autoradio_send_today else 0, # send today = 1.
                    'Cierre': 1 if picking.autoradio_close_shipping else 0, # 0 or 1. Cerrar envío.
                    'FormaCobroReembolso': picking.autoradio_cash_on_delivery_payment if picking.autoradio_cash_on_delivery_payment else 9, # 9 - Efectivo, 10 - Cheque/Pagaré, 11 - Cheque a la vista, 12- Indiferente.
                    'Cheque1': picking.autoradio_check_1_amount if picking.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha1': picking.autoradio_check_1_date.strftime('%Y/%m/%d %H:%M') if picking.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque2': picking.autoradio_check_2_amount if picking.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha2': picking.autoradio_check_2_date.strftime('%Y/%m/%d %H:%M') if picking.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque3': picking.autoradio_check_3_amount if picking.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha3': picking.autoradio_check_3_date.strftime('%Y/%m/%d %H:%M') if picking.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque4': picking.autoradio_check_4_amount if picking.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha4': picking.autoradio_check_4_date.strftime('%Y/%m/%d %H:%M') if picking.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Desembolso': picking.autoradio_payment, # Importe de los portes?
                    'Referencia': picking.name
                }
            
                res = client.service.WSAgregarBulto(**agregarBulto, _soapheaders=[header])

                if res:
                    picking.carrier_tracking_ref = res[1]
                    picking.autoradio_ccbb = res[2]
                    picking.autoradio_channelling = res[3]
                    picking.autoradio_ccbb_type = res[4]
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))
    

    def WSObtenerDatosHojaRecogida(self, client_code=False, date=False):

        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)

                obtenerDatosHojaRecogida = {
                    'Fecha': date if date else datetime.now().strftime('%d/%m/%Y'),
                    'LoginCliente': self.soap_persona_ordena,
                    'IdEmpresa': client_code if client_code else self.soap_client_code
                }
            
                res = client.service.WSObtenerDatosHojaRecogida(**obtenerDatosHojaRecogida, _soapheaders=[header])
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def WSObtenerDatosHojaRecogidaCentro(self, center_code=False, client_code=False, date=False):

        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)

                obtenerDatosHojaRecogidaCentro = {
                    'Fecha': date if date else datetime.now().strftime('%d/%m/%Y'),
                    'LoginCliente': self.soap_persona_ordena,
                    'IdEmpresa': client_code if client_code else self.soap_client_code,
                    'CodCentro': center_code if center_code else self.soap_center
                }
            
                res = client.service.WSObtenerDatosHojaRecogidaCentro(**obtenerDatosHojaRecogidaCentro, _soapheaders=[header])
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def WSOrdenarRecogida(self, picking=False):
        if not picking:
            raise UserError(_("You need to select a picking to calculate the estimated shipping cost."))

        config = self.search([('soap_url', '!=', None)])
        self = self.browse(config.id)

        client, history = self.create_client()
        if client:
            try:
                header = self.getWSRequestHeader(client)

                ordenarRecogida = {
                    'LoginCliente': self.soap_persona_ordena,
                    'CodCliente': self.soap_client_code,
                    'CodCentro': self.soap_center,
                    'FechaRecogida': picking.scheduled_date.strftime('%Y/%m/%d %H:%M'),
                    'HoraDesdeRecogida': '',
                    'HoraHastaRecogida': '',
                    'CodServicio': picking.carrier_id.autoradio_service_code,
                    # Sender
                    'Remitente': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.name,
                    'CifRemi': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.vat,
                    'DireccionRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **"{}, {}".format(picking.company_id.street, picking.company_id.street2),
                    'PoblacionRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.city,
                    'CodPosRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.zip.zfill(5),
                    'CodPosPorRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **000,
                    'PaisRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **'ESP' if picking.company_id.country_id.code == 'ES' else 'POR' if picking.company_id.country_id.code == 'PT' else False,
                    'MailRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.email or '',
                    'TlfRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **picking.company_id.phone or '',
                    'MovilRem': '', # Si se envía un string vacío lo rellena Autoradio de la ficha de cliente. **'',
                    # Recipient
                    'Destinatario': picking.partner_id.name,
                    'CifDes': picking.partner_id.vat or '',
                    'DireccionDes': "{}, {}".format(picking.partner_id.street or '', picking.partner_id.street2 or ''),
                    'PoblacionDes': picking.partner_id.city,
                    'CodPosDes': picking.partner_id.zip.zfill(5) if picking.partner_id.country_id.code == 'ES' else picking.partner_id.zip.split("-")[0].zfill(0) if picking.partner_id.country_id.code == 'PT' else False,
                    'CodPosPorDes': '000' if picking.partner_id.country_id.code == 'ES' else picking.partner_id.zip.split("-")[1].zfill(0) if picking.partner_id.country_id.code == 'PT' else False,
                    'PaisDes': 'ESP' if picking.partner_id.country_id.code == 'ES' else 'POR' if picking.partner_id.country_id.code == 'PT' else False,
                    'MailDes': picking.partner_id.email or '',
                    'TlfDes': picking.partner_id.phone or '',
                    'MovilDes': picking.partner_id.mobile or '',
                    'ContactoDes': picking.partner_id.name,
                    # Other data
                    'Bultos': picking.number_of_packages,
                    'Kilos': picking.shipping_weight,
                    'TipoPorte': picking.autoradio_type, # P for paid, D for debt
                    'Reembolso': picking.autoradio_refund_amount, # Amount in EUR
                    'TipoComision': picking.autoradio_refund_type, # P for paid, D for debt
                    'Obser': picking.autoradio_obs if picking.autoradio_obs else '', # Comments
                    'AmpliaObser': picking.autoradio_obs_extra if picking.autoradio_obs_extra else '',
                    'RefCliente': picking.partner_id.ref, # ref client
                    'InstOp': picking.carrier_id.autoradio_delivery_instructions,
                    'PersonaOrdena': self.soap_persona_ordena,
                    'FlagEnviarHoy': 1 if picking.autoradio_close_shipping or picking.autoradio_send_today else 0, # send today = 1.
                    'Cierre': 1 if picking.autoradio_close_shipping else 0, # 0 or 1. Cerrar envío.
                    'FormaCobroReembolso': picking.autoradio_cash_on_delivery_payment if picking.autoradio_cash_on_delivery_payment else 9, # 9 - Efectivo, 10 - Cheque/Pagaré, 11 - Cheque a la vista, 12- Indiferente.
                    'Cheque1': picking.autoradio_check_1_amount if picking.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha1': picking.autoradio_check_1_date.strftime('%Y/%m/%d %H:%M') if picking.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque2': picking.autoradio_check_2_amount if picking.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha2': picking.autoradio_check_2_date.strftime('%Y/%m/%d %H:%M') if picking.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque3': picking.autoradio_check_3_amount if picking.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha3': picking.autoradio_check_3_date.strftime('%Y/%m/%d %H:%M') if picking.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Cheque4': picking.autoradio_check_4_amount if picking.autoradio_cash_on_delivery_payment in [10] else 0.0, # Se rellena si FormaCobroReembolso es 10
                    'Fecha4': picking.autoradio_check_4_date.strftime('%Y/%m/%d %H:%M') if picking.autoradio_cash_on_delivery_payment in [10] else '', # Se rellena si FormaCobroReembolso es 10
                    'Desembolso': picking.autoradio_payment, # Importe de los portes?
                    'Referencia': picking.name
                }
            
                res = client.service.WSOrdenarRecogida(**ordenarRecogida, _soapheaders=[header])
                
            except Exception as e:
                raise AccessError(_("Access error message: {}".format(e)))
        else:
            raise AccessError(_("Not possible to establish a client."))

    def send(self):
        self.WSBuscadorEnvio()
