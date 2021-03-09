#!/usr/bin/env python3
import os
from os import scandir
from os.path import abspath
from os.path import join
import base64
import csv
import re

session.open(db='DISMAC')



lines = session.env["account.invoice.line"].search(
    [
        ("invoice_id.type", "in", ("out_invoice", "out_refund")),
    ]
)
nlineas = len(lines)
print("%d"%nlineas)
procesadas=0
pattern = re.compile("1.*")
cambiadas = 0
for line in lines:
  procesadas = procesadas + 1
  print("Procesando Factura %d de %d" % (procesadas, nlineas))
  if len(line.analytic_tag_ids) > 1:
    print("Cambiando etiquetas de factura")
    tag_ids = []
    for tag in line.analytic_tag_ids.filtered(lambda r: not pattern.search(r.name)):
      tag_ids.append(tag.id)
    rec = line.env['account.analytic.default'].account_get(
      line.product_id.id,
      line.invoice_id.commercial_partner_id.id,
      line.invoice_id.user_id.id or line.env.uid,
      line.invoice_id.date,
      company_id=line.company_id.id
    )
    
    if rec:
      tag_ids.extend(rec.analytic_tag_ids.ids)
      line.write({'analytic_tag_ids': [(6, 0, tag_ids)]})
      cambiadas = cambiadas + 1
      print("Cambiada Factura %d " % (cambiadas))
print ("ACABADAS FACTURAS %d" % (cambiadas))    

moves = session.env["account.move.line"].search(
    [
        ("move_id.move_type", "in", ('receivable', 'receivable_refund')),
    ]
)
nlineas = len(moves)
print("%d"%nlineas)
procesadas = 0
cambiadas = 0
pattern = re.compile("1.*")
for move in moves:
  procesadas = procesadas + 1
  print("Procesando Apuntes %d de %d" % (procesadas, nlineas))
  if len(move.analytic_tag_ids) > 1:
    print("Cambiando etiquetas de apunte")
    tag_ids = []
    for tag in move.analytic_tag_ids.filtered(lambda r: not pattern.search(r.name)):
      tag_ids.append(tag.id)
    rec = move.env['account.analytic.default'].account_get(
      move.product_id.id,
      move.move_id.partner_id.id,
      move.invoice_id.user_id.id or move.env.uid,
      move.invoice_id.date,
      company_id=move.company_id.id
    )
    if rec:
      tag_ids.extend(rec.analytic_tag_ids.ids)
      move.write({'analytic_tag_ids': [(6, 0,  tag_ids)]})
      cambiadas = cambiadas + 1
      print("Cambiado Apunte %d " % (cambiadas))
print ("ACABADOS APUNTES %d" % (cambiadas))
session.cr.commit()
exit()
