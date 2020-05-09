#!/usr/bin/env python3
import os
from os import scandir
from os.path import abspath
from os.path import join
import base64

session.open(db='odoo_12_DISMAC_07_05')
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))

#path = '/home/santi/Documentos/DISMAC/IMPORTACION/2019-12
# -18_Fotos_Articulos_Dismac_Enviados_a_Comunitea'
path = '/home/santi/Documentos/DISMAC/WEB/A_Subir'
not_found = []
dir = os.scandir(path)
for arch in dir:
    if arch.is_file():
        arch_name = arch.name
        name = arch_name[0:arch_name.rfind(".")]
        name_up = name.upper()

        domain = ['|', '|', '|',
                      ('default_code', '=', name), ('default_code', '=', name_up),
                      ('catalogue_code', '=', name),
                      ('catalogue_code', '=', name_up)]
        products = session.env['product.product'].search(domain)
        if products:
            with open(join(path, arch_name), "rb") as f:
                data = f.read()
                products[0].write({'image_medium': base64.encodestring(
                    data).decode()})
        else:
            not_found.append(arch_name)

output_file = open(script_path + '/productos_no_encontrados.csv', 'w')
for arch in not_found:
    output_file.write(arch + '\n')
dir.close()
session.cr.commit()
exit()