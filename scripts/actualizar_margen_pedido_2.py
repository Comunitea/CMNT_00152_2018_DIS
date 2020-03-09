#!/usr/bin/env python3

session.open(db='odoo_12_DISMAC_14_02')

domain = [('state', 'in', ('sale', 'done')), ('margin' , '<', 0), ('id', '=', 7722)]
lineas = session.env['sale.order'].search(domain)
count = 0
print(len(lineas))
for rec in lineas:
    rec.order_line._product_margin()
    rec._product_margin()
    rec._product_margin_perc()
    count += 1 
    print (count)

    for line in rec.order_line:
        print(line.purchase_price)

session.cr.commit()
exit()