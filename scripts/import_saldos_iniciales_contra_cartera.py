#!/usr/bin/env python3
import os
from os import scandir
from os.path import abspath
from os.path import join
import base64
from odoo.exceptions import UserError

from datetime import datetime
import pandas

session.open(db='odoo_12_DISMAC_IMPORT')
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))


excel_file = 'Balance_sumas_y_saldos_a_31-Dic-2019.xls' 
journal_id = 3
company_id = 1
fecha = '31/12/2019'
nombre = "Saldos 2019"
asiento_cartera_clientes = 7817
asiento_cartera_proveedores = 7818
asiento_cartera_acreedores = 7819

processed = 0

account = session.env['account.account'].search([('code', '=', '43000001')])
lines = []

df = pandas.read_excel(script_path+"/"+excel_file)

for row in df.index:
    cuenta = df["Cuenta"][row]
    if cuenta == 40000001:
        cuenta = '40000000'
    if cuenta == 41000001:
        cuenta = '41000000'
    if cuenta == 43000001:
        cuenta = '43000000'
    print (cuenta)
    account = session.env['account.account'].search([('code', '=', cuenta), ('company_id', '=', company_id )])
    if not account:
        print("No encontrado [%s]" % (cuenta))
        #raise UserError(_('Cuenta no encontrada'))
    print(account.name)
    saldo = df["Saldo"][row]
    if saldo < 0 :
        debe = 0 
        haber = -1 * saldo
    else:
        debe = saldo
        haber = 0
        
    if cuenta == '43000000':
        apuntes_cartera_43 = session.env['account.move.line'].search([('move_id', '=', asiento_cartera_clientes), 
                                                                      ('account_id', '=', account.id )])
        saldo_cartera = sum(x.debit for x in apuntes_cartera_43) - sum(x.credit for x in apuntes_cartera_43)
        print("SALDO CARTERA 430 [%f]" % (saldo_cartera))
        if saldo_cartera  > 0:
            debe = debe - saldo_cartera
        else:
            haber = haber + saldo_cartera

            
    if cuenta == '41000000':
        apuntes_cartera_41 = session.env['account.move.line'].search([('move_id', '=', asiento_cartera_acreedores), 
                                                                      ('account_id', '=', account.id )])
        saldo_cartera = sum(x.debit for x in apuntes_cartera_41) - sum(x.credit for x in apuntes_cartera_41)
        print("SALDO CARTERA 410 [%f]" % (saldo_cartera))
        if saldo_cartera  > 0:
            debe = debe - saldo_cartera
        else:
            haber = haber + saldo_cartera
            
    if cuenta == '40000000':
        apuntes_cartera_40 = session.env['account.move.line'].search([('move_id', '=', asiento_cartera_proveedores), 
                                                                      ('account_id', '=', account.id )])
        saldo_cartera = sum(x.debit for x in apuntes_cartera_40) - sum(x.credit for x in apuntes_cartera_40)
        print("SALDO CARTERA 400 [%f]" % (saldo_cartera))
        if saldo_cartera  > 0:
            debe = debe - saldo_cartera
        else:
            haber = haber + saldo_cartera
    
    lines.append(
        (0, 0, {
                'debit': debe,
                'credit': haber,
                'account_id': account.id
            })
    )
    
    processed += 1
    print("Lineas ejecutadas: %d" % (processed) )
print ("Todas las lineas procesadas")

move_id = session.env['account.move'].create(
    {
        'journal_id': journal_id,
        'date': fecha,
        #'company_id', company_id
        'line_ids': lines,
        'ref':nombre,
    }
)
print ("Creado movimiento")

print("Moviendo apuntes de cartera al asiento")
apuntes_mover = apuntes_cartera_43 | apuntes_cartera_41 | apuntes_cartera_40

apuntes_mover.mapped('move_id').button_cancel()
apuntes_mover.write({'move_id': move_id.id})      

session.cr.commit()
exit()