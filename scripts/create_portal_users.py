#!/usr/bin/env python3
import os
from os import scandir
from os.path import abspath
from os.path import join
import base64
import csv

session.open(db='odoo_12_DISMAC_19_05')
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))

path = '/home/santi/Documentos/DISMAC/WEB/'
path_csv = '/home/santi/Documentos/DISMAC/WEB/' \
           'clientes_acceso Final_Imp.csv'
processed = 0

no_encontrados = []
no_validador = []
company_id = 1
with open(path_csv, 'r') as file:
    reader = csv.reader(file, delimiter=',')
    for row in reader:
        parent_id = False
        partner_id = False
        partner = False
        processed += 1
        login = row[1]
        print("================================")
        print("Procesando %d -- [%s]" % (processed, login))

        user =  session.env['res.users'].search([('login', '=', login)] , limit=1)    
        partner_ref = row[2]
        name = row[4]
        password = row[7]
        email = row[20]
        enviarpedidos = row[13]
        principal  = row[6] == '1' or False
        
        show_customer_price = row[8] == '1' or False
        show_invoices = row[9] == '1' or False
        if row[10] == '1':
            website_acces_rights = 'all'
        else:
            website_acces_rights = 'own'
        show_history = row[8] == '1' or False
        skip_website_checkout_payment = True
        wholesaler = row[19] == '1' or False
        if not user:    
            # No hay usuario 
            print("Preparando para crear usuario")
            s_login = login.replace('_', '-')
            t_logins = s_login.split('-')
            if len(t_logins) > 1:
                t_login = t_logins[0] + "-" + str(int(t_logins[1]))
                domain = ['|', '|', '|',
                        ('ref', '=', s_login.lower()), 
                        ('ref', '=', s_login.upper()),
                        ('ref', '=', t_login.lower()),
                        ('ref', '=', t_login.upper()),
                        ]
            else:
                domain = ['|', 
                        ('ref', '=', s_login.lower()), 
                        ('ref', '=', s_login.upper())]
            
        
            # buscamos indiferente mayusculas y minusculas y pasamos la _ a - 
            # PENDIENTE el camiar -0* por -* pero no parece del todo fiable esta busqueda
            partner = session.env['res.partner'].search(domain, limit=1)
            if partner:
                # si encontramos partner con referencia igual al login
                # ese será del que colgamso nuesro usuario

                parent_id = partner
            elif email:
                # si no lo encontramos, si hay correo tratamos de  buscar un partner hijo del tipo contacto del princiapel con ese mail
                # al que asignarle el usuario de web
                # Buscamos el principal
                new_domain = ['|', ('ref', '=', partner_ref.lower()), ('ref', '=', partner_ref.upper())]
                partner_parent  = session.env['res.partner'].search(new_domain, limit=1)
                
                if partner_parent:
                    domain_mail = [('id', 'child_of', partner_parent.id, ),
                                     ('email', '=', email), 
                                     ('type', '=', 'contact'),
                                     ('is_company', '=', False)]
                    partner_mail = session.env['res.partner'].search(domain_mail, limit=1)
                    if partner_mail:
                        partner_id = partner

            # TERMINAMOS LA Búsqueda del parent

            if parent_id:
                #Si enconcontramos  de donde colgarlo
                print("PARTNER LOCALIZADO para NUEVO [%s]%s - id:%d" %(parent_id.ref, parent_id.name, parent_id.id))
                user = session.env['res.users'].with_context(no_reset_password=True)._create_user_from_template({
                        'login': login,
                        'name': name,
                        'parent_id': parent_id.id,
                        'company_id': company_id,
                        'company_ids': [(6, 0, [company_id])],
                        'password': password,
                        'show_history': show_history,
                        'show_customer_price': show_customer_price,
                        'show_invoices': show_invoices,
                        'main_user': principal,
                        'skip_website_checkout_payment': skip_website_checkout_payment,
                        'website_access_rights': website_acces_rights,
                        'wholesaler': wholesaler,
                        'portfolio': True,
                        'company_type': 'person',
                        'type': 'contact',
                        'email': email
                    })
                print ("Creado usuario y partner con sus permisos (id: %d)" % user.partner_id.id)
            elif partner_id:
                print("PARTNER LOCALIZADO para ACTUALIZAR [%s]%s" %(parent_id.ref, parent_id.name))
                user = session.env['res.users'].with_context(no_reset_password=True)._create_user_from_template({
                        'login': login,
                        'partner_id': partner_id.id,
                        'company_id': company_id,
                        'company_ids': [(6, 0, [company_id])],
                        'password': password,
                        'show_history': show_history,
                        'show_customer_price': show_customer_price,
                        'show_invoices': show_invoices,
                        'main_user': principal,
                        'skip_website_checkout_payment': skip_website_checkout_payment,
                        'website_access_rights': website_acces_rights,
                        'wholesaler': wholesaler,
                        'portfolio': True,
                    })
                print ("Creado usuario y partner ACTULIZADO con sus permisos")
            else:
                print("ERROR: PARTNER no encontrado para %s " % login)
                no_encontrados.append(row)
        else:
            print("Ya existe este usuario, porobamos si necesita validador o si ya lo tiene")
            #Actualizamos valoreS:
            user.write({
                'login': login,
                'company_id': company_id,
                'company_ids': [(6, 0, [company_id])],
                'password': password,
                'show_history': show_history,
                'show_customer_price': show_customer_price,
                'show_invoices': show_invoices,
                'main_user': principal,
                'skip_website_checkout_payment': skip_website_checkout_payment,
                'website_access_rights': website_acces_rights,
                'wholesaler': wholesaler,
                'portfolio': True,
            }
            )
            
        if enviarpedidos != '1' and not user.global_order_validator :
            # NO PUEDE ENVIAR PEDIDO, NECESITA VALIDADOR y NO LO TIENE
            # comprobar validador
            # busca empresa principal
            print ("Necesita validador y no tiene asignado")

            # Busca validador (usuario marcado como principal con el login de la referencia principal)
            user_val = False
            partner_val = session.env['res.partner'].search([('id', 'child_of', user.partner_id.commercial_partner_id.id), ('main_user', '=', True)], limit=1)
            if partner_val and partner_val.user_ids:
                user_val = partner_val.user_ids[0]
            if user_val:
                # tiene usario con login = partner ref y se lo asignamos a l aempresa padre
                user.commercial_partner_id.order_validator = user_val[0].id
                user.commercial_partner_id.create_tier_definition() # Aseguramso que se cree la regla
                print ("Encuentra usuario con login principal y se lo asigna como validador para %s " % login)
            else:
                # No hay usuario 
                
                print("ERROR. El partner deberia tener validador y no se ha encontrado un partne PRINCIPAL")
                no_validador.append(row)
                                            
            
with open('partner_not_found_final.csv', 'a') as partner_not_found:
    for ne in no_encontrados:
        writer_pnf = csv.writer(partner_not_found)
        writer_pnf.writerow(ne)
with open('partner_not_validator_final.csv', 'a') as partner_not_validator:
    for nv in no_validador:
        writer_pnv = csv.writer(partner_not_validator)
        writer_pnv.writerow(row)     


session.cr.commit()
#exit()