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
path_csv = '/home/santi/Documentos/DISMAC/IMPORTACION/cartera/Cartera_para_importar.csv' 
file_not_found = []
partner_not_found = []

processed = 0
mandate_not_found = []
partner_not_found = []
account = session.env['account.account'].search([('code', '=', '43000001')])
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
        credit =0 
        debit =  float(row[11].replace(',','.'))
        if debit < 0:
            credit = -1 * debit
            debit = 0
        if row[12] == '': 
            blocked = False
        else:
            blocked = True
        partner_bank = row[17]
        mandate_cod = row[16]

        domain = [('ref', '=', partner_ref)]
       
        partners = session.env['res.partner'].search(domain)
        domain = [('name', '=', payment_mode)]
        payment_mode = session.env['account.payment.mode'].search(domain)
        bank_xml_id = "__import__."+partner_bank
        

        if partners:
            if mandate_cod != '':
                nif = partners[0].vat
                nif = nif[-9:] 
                mandate_xml_id = bank_xml_id + "_" + nif
                try:
                    mandate = session.env.ref(mandate_xml_id)
                except:
                    print ("Mandato no encontrado: " + mandate_cod )
                    mandate = False
                    mandate_not_found.append(mandate_cod)
            else:
                mandate = False
            data_dict = {
                'name': name,
                'debit': debit,
                'credit': credit,
                'date': date_str,
                'date_maturity': date_maturity_str,
                'blocked': blocked,
                'partner_id': partners[0].id,
                'mandate_id': mandate and mandate.id or False,
                'account_id': account.id,
                'move_id': 3741
            }
            session.env['account.move.line'].create(data_dict)
            print("Lineas ejecutadas: %d" % (processed) )
           
            
        else:
            print("ERROR: Fila no procesada %d" % (processed))
            partner_not_found.append(partner_ref)
        
output_file = open(script_path + '/partners_no_encontrados.csv', 'w')
for arch in partner_not_found:
    output_file.write(arch + '\n')
output_file = open(script_path + '/mandates_no_encontrados.csv', 'w')
for arch in mandate_not_found:
    output_file.write(arch + '\n'

session.cr.commit()
exit()