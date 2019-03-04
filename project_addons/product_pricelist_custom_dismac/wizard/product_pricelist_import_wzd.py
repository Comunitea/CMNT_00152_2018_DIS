# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import datetime, xlrd
import base64
from pprint import pprint
from odoo import exceptions

class PricelistImportWzd(models.TransientModel):
    _name = "product.pricelist.import.wzd"

    file = fields.Binary(string="File", required=True)

    def _parse_row_vals(self, row, idx):
            
        res = {
            'catalogue_code': row[0],
            'name': 'PROMOTION ' + row[40],
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
        error_msg = ""

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
                    
                # Creamos el product_pricelist con los datos del primer row
                if not product_pricelist_obj:
                    product_pricelist_obj = self.create_new_product_pricelist(row_vals['name'], row_vals['date_start'], row_vals['date_end'])

                # Buscamos si existe algún producto (product.product) donde el campo ean13_str contenga el ean
                product_obj = self.env['product.product'].search([('catalogue_code', '=', row_vals['catalogue_code']), ('catalogue_code', '!=', False)])

                if product_obj and len(product_obj) == 1:
                    if row_vals['c1'] and row_vals['pvp1']:
                        self.create_new_product_pricelist_item(row_vals['c1'], row_vals['pvp1'], product_obj, product_pricelist_obj, row_vals['date_start'], row_vals['date_end'])
                    
                    if row_vals['c2'] and row_vals['pvp2']:
                        self.create_new_product_pricelist_item(row_vals['c2'], row_vals['pvp2'], product_obj, product_pricelist_obj, row_vals['date_start'], row_vals['date_end'])
                    
                    if row_vals['c3'] and row_vals['pvp3']:
                        self.create_new_product_pricelist_item(row_vals['c3'], row_vals['pvp3'], product_obj, product_pricelist_obj, row_vals['date_start'], row_vals['date_end'])
                    
                    if row_vals['c4'] and row_vals['pvp4']:
                        self.create_new_product_pricelist_item(row_vals['c4'], row_vals['pvp4'], product_obj, product_pricelist_obj, row_vals['date_start'], row_vals['date_end'])
                else:
                    if len(product_obj) != 1:
                        error_msg = _("There are %s products with the catalogue_code: %s. You may check this out.\n") % (len(product_obj), row_vals['catalogue_code'])
                        self.create_new_error_line(error_msg, product_pricelist_obj.id)

        return self.view_product_pricelist(product_pricelist_obj.id)

    def create_new_product_pricelist_item(self, quantity, price, product_obj, product_pricelist_obj, date_start, date_end):
        product_pricelist_item_obj = self.env['product.pricelist.item'].create({
            'product_tmpl_id': product_obj.id,
            'applied_on': '0_product_variant',
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
            'item_ids': [],
            'sequence': 1,
            'is_promotion': True
        })
        return product_pricelist_obj
    
    @api.multi
    def view_product_pricelist(self, id):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id ref="product_pricelist_import_wzd_view"': '',
            'res_id': id,
            'target': 'self',
        }
    
    @api.multi
    def create_new_error_line(self, error_msg, id):
        error_obj = self.env['product.pricelist.import.error'].create({
            'import_id': id,
            'error_msg': error_msg
        })

    class PricelistImportError(models.Model):
        _name = "product.pricelist.import.error"

        import_id = fields.Many2one('product.pricelist', 'Pricelist Import', ondelete="cascade")
        error_msg = fields.Text()