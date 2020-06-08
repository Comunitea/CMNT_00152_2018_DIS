#!/usr/bin/env python3

session.open(db='odoo_12_DISMAC_26_05')


products = session.env['product.product'].search([])
count = 0
print(len(products))
for rec in products:
    rec._set_last_purchase_fixed()
    count += 1 
    print (count)

session.cr.commit()
exit()