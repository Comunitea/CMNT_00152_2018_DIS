# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import datetime, xlrd
import base64
from pprint import pprint

class PricelistImportWzd(models.TransientModel):
    _name = "product.pricelist.import.wzd"

    file = fields.Binary(string="File", required=True)
    pricelist_id = fields.Many2one("product.pricelist", ondelete="cascade")
    name = fields.Char(related="pricelist_id.name")
    date_start = fields.Date(related="pricelist_id.date_start")
    date_end = fields.Date(related="pricelist_id.date_end")
    sequence = fields.Integer(related="pricelist_id.sequence")
    discount_policy = fields.Selection(related="pricelist_id.discount_policy")
    active = fields.Boolean(related="pricelist_id.active")
    item_ids = fields.One2many(related="pricelist_id.item_ids")

    def _parse_row_vals(self, row, idx):
            
        res = {
            'catalogue_code': row[0],
            'name': row[40],
            'date_start': row[41],
            'date_end': row[42],
            'c1': row[46],
            'pvp1': row[48],
            'c2': row[49],
            'pvp2': row[51],
            'c3': row[52],
            'pvp3': row[54],
            'c4': row[55],
            'pvp4': row[57],
        }

        # Check mandatory values setted
        if not row[0]:
            row[0] = False
            #raise UserError(
            #    _('Missing EAN in row %s ') % str(idx))
        return res

    def import_pricelist(self):
        self.ensure_one()

        product_pricelist_obj = []
        product_pricelist_items_list = []

        file = base64.b64decode(self.file)
        book = xlrd.open_workbook(file_contents=file)
        sh = book.sheet_by_index(0)
        pricelist_items_ids = []
        idx = 3
        for nline in range(3, sh.nrows):

            idx += 1

            row = sh.row_values(nline)

            date_start = sh.cell_value(rowx=nline, colx=41)
            row[41] = datetime.datetime(*xlrd.xldate_as_tuple(date_start, book.datemode))
        
            date_end = sh.cell_value(rowx=nline, colx=42)
            row[42] = datetime.datetime(*xlrd.xldate_as_tuple(date_end, book.datemode))

            if row[0]:

                row_vals = self._parse_row_vals(row, idx)

                #if row_vals['ean_ud'] == "" or row_vals['ean_ud'] == 'FIN' or len(row_vals['ean_ud']) < 1:
                #    break
                    
                # Creamos el product_pricelist con los datos del primer row
                if not product_pricelist_obj:
                    product_pricelist_obj = self.create_new_product_pricelist(row_vals['name'], row_vals['date_start'], row_vals['date_end'])

                # Buscamos si existe algún producto (product.product) donde el campo ean13_str contenga el ean
                product_obj = self.env['product.product'].search([('catalogue_code', '=', row_vals['catalogue_code']), ('catalogue_code', '!=', False)])

                if product_obj:
                    if row_vals['c1'] and row_vals['pvp1']:
                        self.create_new_product_pricelist_item(row_vals['c1'], row_vals['pvp1'], product_obj, product_pricelist_obj, row_vals['date_start'], row_vals['date_end'])
                    
                    if row_vals['c2'] and row_vals['pvp2']:
                        self.create_new_product_pricelist_item(row_vals['c2'], row_vals['pvp2'], product_obj, product_pricelist_obj, row_vals['date_start'], row_vals['date_end'])
                    
                    if row_vals['c3'] and row_vals['pvp3']:
                        self.create_new_product_pricelist_item(row_vals['c3'], row_vals['pvp3'], product_obj, product_pricelist_obj, row_vals['date_start'], row_vals['date_end'])
                    
                    if row_vals['c4'] and row_vals['pvp4']:
                        self.create_new_product_pricelist_item(row_vals['c4'], row_vals['pvp4'], product_obj, product_pricelist_obj, row_vals['date_start'], row_vals['date_end'])

        self.update({
            'pricelist_id': product_pricelist_obj.id
        })

        product_pricelist_obj.update({
            'item_ids': product_pricelist_items_list
        })

        return self.view_product_pricelist(product_pricelist_obj.id)

    def create_new_product_pricelist_item(self, quantity, price, product_obj, product_pricelist_obj, date_start, date_end):
        product_pricelist_item_obj = self.env['product.pricelist.item'].create({
            'product_tmpl_id': product_obj.product_tmpl_id.id,
            'applied_on': '1_product',
            'base': 'list_price',
            'pricelist_id': product_pricelist_obj.id,
            'min_quantity': quantity,
            'date_start': date_start,
            'date_end': date_end,
            'compute_price': 'fixed',
            'fixed_price': price
        })
        return product_pricelist_item_obj.id
        

    def create_new_product_pricelist(self, name, date_start, date_end):
        product_pricelist_obj = self.env['product.pricelist'].create({
            'name': name,
            'date_start': date_start,
            'date_end': date_end,
            'active': True,
            'selectable': False,
            'discount_policy': 'with_discount',
            'item_ids': []
        })
        return product_pricelist_obj
    
    @api.multi
    def view_product_pricelist(self, product_pricelist_id):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist.import.wzd',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_id': 'action_product_pricelist_import_tree'
        }