#!/usr/bin/env python3
import os
from os import scandir
from os.path import abspath
from os.path import join
import base64
import csv

session.open(db='odoo_12_DISMAC_07_05')
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))

#path = '/home/santi/Documentos/DISMAC/IMPORTACION/2019-12
# -18_Fotos_Articulos_Dismac_Enviados_a_Comunitea'
path = '/home/santi/Documentos/DISMAC/WEB/'
path_csv = '/home/santi/Documentos/DISMAC/WEB/' \
           'clientes_acceso_importa_1.csv'
processed = 0

no_encontrados = []
no_validador = []

with open(path_csv, 'r') as file:
    reader = csv.reader(file, delimiter=',')
    for row in reader:
        processed += 1
        print("================================")
        print(row[1])
        print(processed)
        login = row[1]
        partner_ref = row[2]
        name = row[4]
        password = row[7]
        
        show_customer_price = row[8] == '1' or False
        show_invoices = row[9] == '1' or False
        if row[10] == '1':
            website_acces_rights = 'all'
        else:
            website_acces_rights = 'own'
        show_history = row[8] == '1' or False
        skip_website_checkout_payment = True
        wholesaler = row[19] == '1' or False

        # buscamos indiferente mayusculas y minusculas y pasamos la _ a - 
        # PENDIENTE el camiar -0* por -* pero no parece del todo fiable esta busqueda
        domain = [('ref', '=', login.replace('_', '-').lower()), ('ref', '=', login.replace('_', '-').upper())]
        partner = session.env['res.partner'].search(domain, limit=1)
        if partner:
            
            company_id = 1
            #busca usuario con ese login
            user = session.env['res.users'].search([('login', '=', login)])

            if not user:
                user = session.env['res.users'].with_context(no_reset_password=True)._create_user_from_template({
                        'login': login,
                        'partner_id': partner.id,
                        'company_id': company_id,
                        'company_ids': [(6, 0, [company_id])],
                        'password': password
                    })
                print ("Creado usuario")
            else:
                print ("Usuario ya existe")
            if row[13] != '1':
                # comprobar validador
                # busca empresa principal
                if partner.commercial_partner_id.order_validator:
                    order_validator = None
                    print ("Ya tiene validador")
                else:
                    # el partner padre no tiene validador
                    print ("No tiene validador")
                    user_val = partner.commercial_partner_id.user_ids.filtered(lambda x: x.login == partner_ref)
                    if user_val:
                        # tiene usario con login = partner ref y se lo asignamos a l aempresa padre
                        partner.commercial_partner_id.order_validator = user_val.id
                        print ("Encuentra usuario de commercial partner y se lo asigna como validador")
                    else:
                        # No hay usuario
                        # Lo crea para la empresa padre y se lo asigna como validador
                        print("ERROR. El parner deberñia tener validador y no se ha encontrado")
                        no_validador.appen(row)
                                        


            partner_data_dict = {
                'show_history': show_history,
                'show_customer_price': show_customer_price,
                'show_invoices': show_invoices,
                'skip_website_checkout_payment': skip_website_checkout_payment,
                'website_acces_rights': website_acces_rights,
                'wholesaler': wholesaler,
                'portfolio': True
                
            }
            partner.write(partner_data_dict)
            print("Partner actualizado. Correcto !!")
            
        else:
            print("ERROR: Partner no encontrado)")
            no_encontrados.append(row)
            
with open('partner_not_found.csv', 'a') as partner_not_found:
    for ne in no_encontrados:
        writer_pnf = csv.writer(partner_not_found)
        writer_pnf.writerow(ne)
with open('partner_not_validator.csv', 'a') as partner_not_validator:
    for nv in no_validador:
        writer_pnv = csv.writer(partner_not_validator)
        writer_pnv.writerow(row)     



session.cr.commit()
exit()