#!/usr/bin/env python3
import os
from os import scandir
from os.path import abspath
from os.path import join
import base64
from odoo.exceptions import UserError
from odoo import fields
from datetime import datetime
import pandas
from time import time

session.open(db='DISMAC')
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))


excel_file = 'Asientos_de_2020.xls' 
company_id = 1


asiento_cartera_saldos = 7817

processed = 0
saldos_ini_id = 42025


account_43 =session.env['account.account'].search([('code', '=', '43000000'),
                                                   ('company_id', '=', company_id)])
account_41 =session.env['account.account'].search([('code', '=', '41000000'),
                                                   ('company_id', '=', company_id)])
account_40 =session.env['account.account'].search([('code', '=', '40000000'),
                                                   ('company_id', '=', company_id)])
lines = []
ml_43 = session.env['account.move.line']
ml_41 = session.env['account.move.line']
ml_40 = session.env['account.move.line']
df = pandas.read_excel(script_path+"/"+excel_file)
asiento_prev = 1
journal_id = False
for row in df.index:
    asiento = df["Asiento"][row]
    cuenta = int(df["Cuenta"][row])
    if cuenta == 40000001:
        cuenta = '40000000'
    elif cuenta == 41000001:
        cuenta = '41000000'
    elif cuenta == 43000001:
        cuenta = '43000000'
        
    print (cuenta)
    account = session.env['account.account'].search([('code', '=', cuenta), ('company_id', '=', company_id )])
    j_id = session.env['account.journal'].search([('default_debit_account_id', '=', account.id)])
    if j_id:
        journal_id = j_id
    
    print(account.name)
    debe = df["Debe"][row]
    haber = df["Haber"][row]
    if pandas.isnull(debe):
        debe =0 
    if pandas.isnull(haber):
        haber =0 
    entidad = df["Entidad"][row]
    nombre = df["Documento Refer."][row]
    ref = df["Núm. Documento"][row]
    fecha = df ["Fecha Entrada"][row]
    
    if not pandas.isnull(entidad) and entidad:
        partner = session.env['res.partner'].search([('ref', '=', entidad),
                                                     ('is_company', '=', True)])
        if not partner:
            nombre = df["Nombre de la Entidad"][row]
            print(nombre)
            partner = session.env['res.partner'].search([('name', '=', nombre),
                                                         ('is_company', '=', True)])
            if not partner:
                nombre = df["Nombre de la Entidad"][row].replace(",","")
                print(nombre)
                partner = session.env['res.partner'].search([('name', '=', nombre),
                                                            ('is_company', '=', True)])
                if not partner:
                    print("No encontrado [%s]" % (entidad))
                    raise UserError('Partner no encontrado')
    else:
        partner = False
        
    if asiento != asiento_prev :
        print("Generando nuevo asiento")
        
        move_id = session.env['account.move'].create(
            {
                'journal_id': journal_move_id.id,
                'date': fecha_move,
                #'company_id', company_id
                'line_ids': lines,
                'ref':ref_move,
            }
        )
        ml_43 = ml_43 | move_id.line_ids.filtered(lambda aml: aml.account_id == account_43)
        ml_41 = ml_41 | move_id.line_ids.filtered(lambda aml: aml.account_id == account_41)
        ml_40 = ml_40 | move_id.line_ids.filtered(lambda aml: aml.account_id == account_40)
        print ("Creado movimiento")
        lines =[]
        asiento_prev = asiento
        if journal_id == journal_move_id:
            journal_id = False
        
    date = datetime.strptime(fecha, '%d/%m/%Y')
    date_str = datetime.strftime(date, '%Y-%m-%d')
    fecha_move = date_str
    ref_move = ref
    journal_move_id = journal_id
    lines.append(
    (0, 0, {
            'debit': debe,
            'credit': haber,
            'account_id': account.id,
            'partner_id': partner and partner[0].id or False,
            'name': nombre
        })
    )
    
    
    processed += 1
    print("Lineas ejecutadas: %d" % (processed) )
    

move_id = session.env['account.move'].create(
    {
        'journal_id': journal_move_id.id,
        'date': fecha_move,
        #'company_id', company_id
        'line_ids': lines,
        'ref':ref_move,
    }
)
ml_43 = ml_43 | move_id.line_ids.filtered(lambda aml: aml.account_id == account_43)
ml_41 = ml_41 | move_id.line_ids.filtered(lambda aml: aml.account_id == account_41)
ml_40 = ml_40 | move_id.line_ids.filtered(lambda aml: aml.account_id == account_40)
print ("Creado movimiento")   

print ("Todas las lineas procesadas")


print ("Preparando conciliación masiva clientes")

ml_43_por_partner = session.env['account.move.line'].read_group([('id', 'in', ml_43.ids)],
                                                                 ['partner_id', 'debit', 'credit'],
                                                                 ['partner_id'])

ml_saldo_inicial_43 = session.env['account.move.line'].search([('account_id', '=', account_43.id),
                                                            ('move_id', '=', saldos_ini_id),
                                                            ('partner_id', '=', False)])
total_registros = len(ml_43_por_partner)
count = 1
for partner in ml_43_por_partner:
    start_time = time()
    # Busca el apunte de la 430 en el saldo inicial sin partner, para trocearlo y conciliarlo
    balance = partner['debit'] - partner['credit']
    debe = -1 * balance
    si_43_apunte = ml_saldo_inicial_43.with_context(recompute=False).copy({'debit': debe,
                                           'partner_id':partner['partner_id'][0],
                                           'date': '2019-12-31'})
    # Para comprobar saldo al final y eliminarlo

    ml_saldo_inicial_43.with_context(recompute=False).debit = ml_saldo_inicial_43.debit - debe
    print("Debe restante=%f" % (ml_saldo_inicial_43.debit))

    # Elementos a conciliar, el nuevo apunte generado contra y todos los del partner
    partner_ml_43 = ml_43.filtered(lambda aml: aml.partner_id.id == partner['partner_id'][0])
    to_reconcile = si_43_apunte | partner_ml_43
    to_reconcile.with_context(recompute=False).reconcile()
    elapsed_time = time() - start_time
    print("Conciliado cliente: %d . %d apuntes.  Tiempo: %0.10f (%d de %d)" % (partner['partner_id'][0], len(to_reconcile), elapsed_time, count, total_registros) )
    count = count + 1
    
    
print ("Preparando conciliación masiva proveedores")

ml_40_por_partner = session.env['account.move.line'].read_group([('id', 'in', ml_40.ids)],
                                                                 ['partner_id', 'debit', 'credit'],
                                                                 ['partner_id'])

ml_saldo_inicial_40 = session.env['account.move.line'].search([('account_id', '=', account_40.id),
                                                            ('move_id', '=', saldos_ini_id),
                                                            ('partner_id', '=', False)])
total_registros = len(ml_40_por_partner)
count = 1
for partner in ml_40_por_partner:
    start_time = time()
    # Busca el apunte de la 400 en el saldo inicial sin partner, para trocearlo y conciliarlo
    balance = partner['debit'] - partner['credit']
    haber = balance
    si_40_apunte = ml_saldo_inicial_40.with_context(recompute=False).copy({'credit': haber,
                                           'partner_id':partner['partner_id'][0],
                                           'date': '2019-12-31'})
    # Para comprobar saldo al final y eliminarlo

    ml_saldo_inicial_40.with_context(recompute=False).credit = ml_saldo_inicial_40.credit - haber
    print("Haber restante=%f" % (ml_saldo_inicial_40.credit))
    # Elementos a conciliar, el nuevo apunte generado contra y todos los del partner
    partner_ml_40 = ml_40.filtered(lambda aml: aml.partner_id.id == partner['partner_id'][0])
    to_reconcile = si_40_apunte | partner_ml_40
    to_reconcile.with_context(recompute=False).reconcile()
    elapsed_time = time() - start_time
    print("Conciliado proveedor: %d . %d apuntes.  Tiempo: %0.10f (%d de %d)" % (partner['partner_id'][0], len(to_reconcile), elapsed_time, count, total_registros) )
    count = count + 1


print ("Preparando conciliación masiva acreedores")

ml_41_por_partner = session.env['account.move.line'].read_group([('id', 'in', ml_41.ids)],
                                                                 ['partner_id', 'debit', 'credit'],
                                                                 ['partner_id'])

ml_saldo_inicial_41 = session.env['account.move.line'].search([('account_id', '=', account_41.id),
                                                            ('move_id', '=', saldos_ini_id),
                                                            ('partner_id', '=', False)])

total_registros = len(ml_41_por_partner)
count = 1
for partner in ml_41_por_partner:
    start_time = time()
    # Busca el apunte de la 430 en el saldo inicial sin partner, para trocearlo y conciliarlo
    balance = partner['debit'] - partner['credit']
    if balance >= 0:
        haber = balance
        debe = 0
        ml_saldo_inicial_41.with_context(recompute=False).credit = ml_saldo_inicial_41.credit - haber
        print("Haber restante=%f" % (ml_saldo_inicial_41.credit))
    else:
        haber = 0
        debe = -1 * balance
        ml_saldo_inicial_41.with_context(recompute=False).debit = ml_saldo_inicial_41.debit - debe
    si_41_apunte = ml_saldo_inicial_41.with_context(recompute=False).copy({'credit': haber,
                                                                           'debit': debe,
                                                                           'partner_id':partner['partner_id'][0],
                                                                           'date': '2019-12-31'})
        
    # Elementos a conciliar, el nuevo apunte generado contra y todos los del partner
    partner_ml_41 = ml_41.filtered(lambda aml: aml.partner_id.id == partner['partner_id'][0])
    to_reconcile = si_41_apunte | partner_ml_41
    to_reconcile.with_context(recompute=False).reconcile()
    elapsed_time = time() - start_time
    print("Conciliado acreedor: %d . %d apuntes.  Tiempo: %0.10f (%d de %d)" % (partner['partner_id'][0], len(to_reconcile), elapsed_time, count, total_registros) )
    count = count + 1

print("TODO CONCILIADO")

session.cr.commit()
exit()
