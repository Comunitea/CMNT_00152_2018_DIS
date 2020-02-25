#!/usr/bin/env python3

session.open(db='odoo_12_DISMAC_14_02')

domain = [('state', 'in', ('sale', 'done'))]
lineas = session.env['sale.order.line'].search(domain)
count = 0
print(len(lineas))
for rec in lineas:
    if rec.product_id.type != 'product' or  rec.product_id.last_purchase_price_fixed == rec.product_id.standard_price:
        print("ACTUALIZANDO MARGEN LINEA")
        rec._product_margin()
    count += 1 
    print (count)

session.cr.commit()
exit()