#!/usr/bin/env python3
import os
from os import scandir
from os.path import abspath
from os.path import join
import base64
import csv

session.open(db='odoo_12_DISMAC_31_01')

script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))

domain = [('state', 'not in', ['cancel', 'draft']),('order_id', '=', 4210)]
lines = session.env['sale.order.line'].search(domain)
deliv_obj = session.env['sale.order.line.delivery']
count = 0
lineas_total = len(lines)
new_deliveries = []
print("Lineas a revisar %d"  % lineas_total)
for sale_line in lines:
    print("%s,%s,%d,%d" % (sale_line.order_id.name, sale_line.product_id.name, sale_line.qty_delivered, sale_line.qty_invoiced))
    for move in sale_line.move_ids.filtered(lambda a: a.state == 'done'):
        delivs = deliv_obj.search(['|', ('quantity', '=', move.product_uom_qty),
                                        ('quantity', '=', -move.product_uom_qty),
                                        ('delivery_date', '=', move.date),
                                        ('line_id', '=', sale_line.id)])
        print("DELIVS: ", delivs)
        if not delivs:
            print ("POSIBLE DELIVERY A CREAR %s" % sale_line.order_id.name)
            if move.state == 'done':
                qty = 0.0
                line = move.sale_line_id
                if move.location_dest_id.usage == "customer":
                    if not move.origin_returned_move_id or \
                            (move.origin_returned_move_id and
                                move.to_refund):
                        qty = move.product_uom._compute_quantity(
                            move.product_uom_qty, move.product_uom)
                elif move.location_dest_id.usage != "customer" and \
                        move.to_refund:
                    qty = -move.product_uom._compute_quantity(
                        move.product_uom_qty, move.product_uom)
                if qty:
                    deliv_obj.create({
                        'line_id': line.id,
                        'quantity': qty,
                        'delivery_date': move.date,
                    })
                    new_deliveries.append("%s,%s,%d" % (sale_line.order_id.name, sale_line.product_id.name, qty ))
                    print ("DELIVERY CREADO PARA %s" % sale_line.order_id.name)
            
        
    count += 1 
    print ("Lineas Restantes: %d" % (lineas_total - count) )

output_file = open(script_path + '/nuevos_deliveries.csv', 'w')
for arch in new_deliveries:
    output_file.write(arch + '\n')
session.cr.commit()
exit()