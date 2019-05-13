# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import xlrd
import base64

import logging
_logger = logging.getLogger(__name__)

# Global variable to store the new created templates
template_ids = []


class StockImportWzd(models.TransientModel):

    _name = 'stock.inventory.import.wzd'

    name = fields.Char('Importation name', required=True)
    inventory_id = fields.Many2one('stock.inventory')
    file = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Filename')

    @api.onchange('file')
    def onchange_filename(self):
        if not self.name and self.filename:
            self.name = self.filename and self.filename.split('.')[0]

    def _parse_row_vals(self, row, idx):
        res = {

            'code': row[0],
            'product_name': row[1],
            'qty': row[2],
            'location_id': row[3],
            #'location_xml_id': row[4],
        }

        return res


    def _get_location_id(self, loc_name=False, idx=0):

        domain=[('name', '=', loc_name)]
        location_id = self.env['stock.location'].search(domain, limit=1)
        return location_id


    def _get_product(self, code):
        domain = [('default_code', '=', code)]
        product_id = self.env['product.product'].search(domain, limit=1)
        return product_id


    def import_products(self):
        
        self.ensure_one()
        _logger.info(_('STARTING PRODUCT IMPORTATION'))

        # get the first worksheet
        file = base64.b64decode(self.file)
        book = xlrd.open_workbook(file_contents=file)
        sh = book.sheet_by_index(0)
        created_product_ids = []
        idx = 1

        for nline in range(1, sh.nrows):
            if idx> 500:
                break
            idx += 1
            row = sh.row_values(nline)
            row_vals = self._parse_row_vals(row, idx)
            qty = row_vals['qty']
            if qty >0:
                location_id = self._get_location_id(row_vals['location_id'])
                product_id = self._get_product(row_vals['code'])
                if location_id and product_id:
                    vals = {'product_id': product_id.id, 'location_id': location_id.id, 'inventory_id': self.inventory_id.id, 'product_qty': qty}
                    self.env['stock.inventory.line'].create(vals)

            _logger.info(_('IMPORTED line %s / %s') % (idx, sh.nrows - 1))


        self.ensure_one()
        action = self.env.ref(
            'stock.action_inventory_form').read()[0]
        action['domain'] = [('id', '=', self.inventory_id.id)]
        return action