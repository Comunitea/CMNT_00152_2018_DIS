#!/usr/bin/env python3

session.open(db='odoo_12_DISMAC_14_01')

domain = [('price', '=', 0)]
pricelists = session.env['product.supplierinfo'].search(domain)
count = 0
print(len(pricelists))
for rec in pricelists:
    if rec.price == 0:
        if rec.product_id: 
            if rec.product_id.last_purchase_price:
                rec.write({'price': rec.product_id.last_purchase_price})
        else:
            if rec.product_tmpl_id:
                if rec.product_tmpl_id.last_purchase_price:
                    rec.write({'price': rec.product_tmpl_id.last_purchase_price})
    count += 1 
    print (count)

session.cr.commit()
exit()