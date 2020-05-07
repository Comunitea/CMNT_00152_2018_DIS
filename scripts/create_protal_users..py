#!/usr/bin/env python3
import os
from os import scandir
from os.path import abspath
from os.path import join
import base64
import csv

session.open(db='odoo_12_DIS_PREPROD')
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))

#path = '/home/santi/Documentos/DISMAC/IMPORTACION/2019-12
# -18_Fotos_Articulos_Dismac_Enviados_a_Comunitea'
path = '/home/santi/Documentos/DISMAC/WEB/'
path_csv = '/home/santi/Documentos/DISMAC/WEB/' \
           'clientes_acceso.csv'
file_not_found = []
partner_not_found = []

processed = 0

with open(path_csv, 'r') as file:
    reader = csv.reader(file, delimiter=';')
    for row in reader:
        processed += 1
        login = row[1]
        partner_ref = row[2]
        name = row[4]
        password = row[7]
        show_customer_price = row[8]
        show_invoices = row[9]
        website_acces_rights = row[10]
        show_history = row[11]
        skip_website_checkout_payment = True

        domain = [('ref', '=', partner_ref)]
        partners = session.env['res.partner'].search(domain)
        if partners:
            try:
                with open(join(path, arch_name), "rb") as f:
                    data = f.read()
                    data_dict = {
                        'datas_fname': arch_name,
                        'name': name,
                        'type': 'binary',
                        'res_model': 'res.partner',
                        'res_id': partners[0].id,
                        'datas':base64.encodestring(data).decode(),
                        'description': name
                    }
                    session.env['ir.attachment'].create(data_dict)
                    print("Correcto")
            except:
                print("ERROR: Archivo no encontrado)")
                file_not_found.append(arch_name)
        else:
            print("ERROR: Partner no encontrado)")
            partner_not_found.append(partner_ref)




output_file = open(script_path + '/partners_no_encontrados.csv', 'w')
for arch in partner_not_found:
    output_file.write(arch + '\n')
output_file = open(script_path + '/files_no_encontrados.csv', 'w')
for arch in file_not_found:
    output_file.write(arch + '\n')
session.cr.commit()
exit()