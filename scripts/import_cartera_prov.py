#!/usr/bin/env python3
import os
from os import scandir
from os.path import abspath
from os.path import join
import base64
import csv
from datetime import datetime

session.open(db='odoo_12_DISMAC_14_02')
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))

#path = '/home/santi/Documentos/DISMAC/IMPORTACION/2019-12
# -18_Fotos_Articulos_Dismac_Enviados_a_Comunitea'
path = '/home/santi/Documentos/DISMAC/IMPORTACION/cartera/'
path_csv = '/home/santi/Documentos/DISMAC/IMPORTACION/cartera/Cartera_para_importar_acreed.csv' 
file_not_found = []
partner_not_found = []

processed = 0

account = session.env['account.account'].search([('code', '=', '41000001')])
with open(path_csv, 'r') as file:
    reader = csv.reader(file, delimiter=';')
    for row in reader:
        processed += 1
        partner_ref = row[2]
        name = row[4]
        date = datetime.strptime(row[5], '%d/%m/%Y')
        date_str = datetime.strftime(date, '%Y-%m-%d')
        date_maturity = datetime.strptime(row[6], '%d/%m/%Y')
        date_maturity_str = datetime.strftime(date_maturity,'%Y-%m-%d')
        payment_mode = row[8]
        debit =0 
        credit =  float(row[11].replace(',','.'))
        if credit < 0:
            debit = -1 * credit
            credit = 0
        if row[12] == '': 
            blocked = False
        else:
            blocked = True
        #partner_bank = row[17]
        #mandate_cod = row[16]

        domain = [('ref', '=', partner_ref)]
       
        partners = session.env['res.partner'].search(domain)
        domain = [('name', '=', payment_mode)]
        payment_mode = session.env['account.payment.mode'].search(domain)
        
        if partners:
            data_dict = {
                'name': name,
                'debit': debit,
                'credit': credit,
                'date': date_str,
                'date_maturity': date_maturity_str,
                'blocked': blocked,
                'partner_id': partners[0].id,
                'account_id': account.id,
                'payment_mode_id': payment_mode and payment_mode.id or False,
                'move_id': 3741
            }
            session.env['account.move.line'].create(data_dict)
            print("Lineas ejecutadas: %d" % (processed) )
           
            
        else:
            print("ERROR: Fila no procesada %d" % (processed))
        

session.cr.commit()
exit()