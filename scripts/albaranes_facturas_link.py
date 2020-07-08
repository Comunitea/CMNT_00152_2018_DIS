#!/usr/bin/env python3
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import fields
import csv


def comprueba(inv, fecha):
    if fecha:
        fecha_str = fields.Date.to_string(fecha)
        invoice_until = fecha_str
    for line in inv.invoice_line_ids:
        sale_lines = line.sale_line_ids
        for sl in sale_lines:
            if not fecha:
                moves = sl.get_stock_moves_link_invoice()
            else:
                moves = sl.with_context(invoice_until=invoice_until).get_stock_moves_link_invoice()
            if moves:
                qty = sum(moves.mapped('quantity_done'))
                if line.quantity > qty:
                    # YA es mayor la cantidad facturado que el enviado
                    return "error"
                    # ERRROR s. SE devuelve fallo directamente
                    
                elif line.quantity < qty:
                    ret_moves = sl.mapped('move_ids').filtered(
                    lambda x: (
                        x.state == 'done' and not (any(
                            inv.state != 'cancel' for inv in x.invoice_line_ids.mapped(
                                'invoice_id'))) and not x.scrapped and (
                            x.location_id.usage == 'customer' )
                        )
                    )
                    
                    if not ret_moves:
                        return False
                    # Consideramos posibles devoluciones sin marcar...
                    ret_qty = sum(ret_moves.mapped('quantity_done'))
                    n_qty = qty - ret_qty
                    if line.quantity < n_qty:
                    # Buscar fecha anterior
                        return False
    return True
                


def comprueba_fecha_correcta(inv, fecha = False):

    res = comprueba(inv, False)
    if res == "error":
        # FACTURA NO RECUPERABLE
        return res
    elif res == True:
        # Válida sin fecha
        return True
    
    # Debemos buscar por fecha
    if not fecha:
        fecha = inv.create_date

    for i in range(30):
        fecha_valida = True
        fecha_str = fields.Date.to_string(fecha)

        #print("Busca fecha %s  (-%d)" % (fecha_str, i))
        res= comprueba(inv, fecha)
        if res == True:
            return fecha
        elif res == "error":
            return res
                
        fecha = fecha + relativedelta(days=-1)
    print ("Fecha no encontrada  hasta %s !!!" % fecha_str)
    return "error"

def regenera(inv, fecha):
    all_moves = session.env['stock.move']
    if fecha:
        fecha_str = fields.Date.to_string(fecha)
        invoice_until = fecha_str
    for line in inv.invoice_line_ids:
        line_moves = session.env['stock.move']
        sale_lines = line.sale_line_ids
        for sl in sale_lines:
            if not fecha:
                moves = sl.get_stock_moves_link_invoice()
            else:
                moves = sl.with_context(invoice_until=invoice_until).get_stock_moves_link_invoice()
            
            line_moves = line_moves | moves
        vals={
            'move_line_ids': [(4, m.id) for m in line_moves]
            }
        line.write (vals)
        all_moves = all_moves | line_moves
    all_moves.mapped('picking_id').write({
        'invoice_ids': [(4, inv.id)],
    })


session.open(db='odoo_12_DISMAC_26_05')
error = []
sin_movimientos = []
regeneradas = []
domain = [
    #('picking_ids', '=', False),
    #('type', '=', 'out_invoice'),
    #('state', 'in', ['open', 'paid']),
    ('id', 'in',  [11781,]),
    #('commercial_partner_id', 'in',  [22880,])

]
todas_facturas = session.env['account.invoice'].search(domain, order="date_invoice ASC")
total = len(todas_facturas)
print("TOTAL FACTURAS: %d" % len(todas_facturas))
num = 1
for inv in todas_facturas:
    fecha = inv.create_date
    print ("FACTURA : %s - %d de %d" % (inv.invoice_number, num, total ))
    sale_lines = inv.invoice_line_ids.mapped('sale_line_ids')
    moves = sale_lines.get_stock_moves_link_invoice()
    if not moves:
        print ("Factura sin movimientos ")
        sin_movimientos.append([inv.invoice_number, fecha])
    else:
        res = comprueba_fecha_correcta(inv, fecha)
        if res == "error":
            print ("ERRRORRRR!!! NO ENLAZABLE la factura '%s' " % inv.invoice_number)
            error.append([inv.invoice_number, fecha])
        else: 
            if res == True:
                print ("COMENZANDO A REGENERAR. SIN FECHA")
                fecha = False
            else:
                print ("COMENZANDO A REGENERAR. CON  FECHA  %s" % res)
                fecha = res
            regenera(inv, fecha)        
            regeneradas.append([inv.invoice_number, fecha])        
    num += 1            

with open('regeneradas.csv', 'a') as regeneradas_csv:
    writer_reg = csv.writer(regeneradas_csv)
    for reg in regeneradas:
        writer_reg.writerow(reg)

with open('error.csv', 'a') as error_csv:
    writer_err = csv.writer(error_csv)
    for err in error:
        writer_err.writerow(err)

with open('sin_movimientos.csv', 'a') as sm_csv:
    writer_sm = csv.writer(sm_csv)
    for sm in sin_movimientos:
        writer_sm.writerow(sm)

session.cr.commit()
exit()


