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

PASILLO = {'A': 0 ,'B': 1 ,'C': 2 ,'D': 4 ,'E': 5 ,'F': 6 ,'G': 7, 'H': 8 ,
           'I': 9 ,'J': 10 ,'K': 11 ,'L': 12 ,'M': 13 ,'N': 14, 'O': 15, 'P': 16,
           'Q': 17, 'R': 18, 'S': 19, 'T': 20, 'U': 21, 'V': 21, 'X': 22, 'Y': 23, 'Z': 24,
           'CIT': 100 ,'ZA': 200 ,'ZB': 201 ,'BE': 100 ,'EM': 300 ,'EXPOS': 500}
LOCATION_IDS = []

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    import_name = fields.Char('Import name')
    import_product_id = fields.Many2one('product.product', 'Producto orig.')


class StockLocation (models.Model):

    _inherit ='stock.location'

    import_name = fields.Char(string="Ubicación importada")
    floor = fields.Integer(string="Piso", default=-1)
    building = fields.Integer(string="Nave", default=-1)

    @api.multi
    def set_barcode(self):

        for location in self:
            parent_loc = location
            while location.floor == -1 and parent_loc:
                location.floor == parent_loc.floor
                parent_loc = parent_loc.location_id

            parent_loc = location
            while location.building == -1 and parent_loc:
                location.building == parent_loc.building
                parent_loc = parent_loc.location_id
            if location.floor != -1 and location.building != -1:
                location.barcode = '%01d.%01d.%03d.%02d.%02d'%(location.building, location.floor, location.posx, location.posy, location.posz)
            _logger.info('Actualizando {}: {}'.format(location.display_name, location.barcode))







class ProductTemplate (models.Model):

    _inherit ='product.template'

    import_location_str = fields.Char(string="Ubicación importada")

class ProductImportWzd(models.TransientModel):

    _name = 'product.import.wzd'

    name = fields.Char('Importation name', required=True)
    file = fields.Binary(string='File', required=True)
    start_line = fields.Integer("Desde linea")
    end_line = fields.Integer("Hasta linea")
    location_id = fields.Many2one('stock.location', 'Ubicación del ajuste')
    filename = fields.Char(string='Filename')

    @api.onchange('file')
    def onchange_filename(self):
        if not self.name and self.filename:
            self.name = self.filename and self.filename.split('.')[0]

    def _parse_rows(self):
        pass

    def _parse_row_vals(self, row, idx):
        res = {
            'default_code': str(row[0]),
            'nombre_articulo': str(row[1]),
            'ubicacion_1': str(row[2]),
            'ubicacion_2': str(row[3]),
            'ubicacion_3': str(row[4]),
            'ubicacion_4': str(row[5]),
            'ubicacion_5': str(row[6]),
            'ubicacion_6': str(row[7]),
            'ubicacion_7': str(row[8]),
            'stock': float(row[9]) or 0.0,
            'cost': float(row[10]) or 0.0,
        }
        # Check mandatory values setted
        if not row[0]:
            raise UserError(
                _('Missing Code in row %s ') % str(idx))

        return res

    def get_pasillo_vals(self, pasillo, planta_id):
        pl_dom = [('location_id', '=', planta_id), '|', ('name', '=', pasillo), ('import_name', '=', pasillo)]
        pasillo_id = self.env['stock.location'].search_read(pl_dom, ['id'], limit=1)

        if not pasillo_id:
            pasillo_vals = {'name': pasillo,
                            'import_name': pasillo,
                            'location_id': planta_id,
                            'usage': 'view'}

            pasillo_id = self.env['stock.location'].create(pasillo_vals)
            LOCATION_IDS.append(pasillo_id)
            _logger.info('SE HA CREADO LA UBIACIÓN: {}'.format(pasillo_id.display_name))
            pasillo_id = pasillo_id.id
        else:
            pasillo_id = pasillo_id[0]['id']

        return pasillo_id

    def  get_loc_vals(self, str):
        def sin_numeros(s):
            numeros = "1234567890"
            s_sin_numeros = ""
            for letra in s:
                if letra not in numeros:
                    s_sin_numeros += letra
            return s_sin_numeros

        if str[:1] == '1':
            str = str[1:]
            domain = [('name', '=', 'Planta 1')]
            planta_id = self.env['stock.location'].search_read(domain, ['id'], limit=1)[0]['id']
        elif str[:1] == 'P':
            domain = [('name', '=', 'Palets')]
            return self.env['stock.location'].search_read(domain, ['id'], limit=1)[0]['id']
        else:
            domain = [('name', '=', 'Planta 0')]
            planta_id = self.env['stock.location'].search_read(domain, ['id'], limit=1)[0]['id']

        name = str
        pasillo = sin_numeros(str)
        pasillo_id = self.get_pasillo_vals(pasillo, planta_id)
        posx = int(PASILLO.get(pasillo, 0))

        n1 = name.replace(pasillo, '')



        if len(n1) > 1:
            posy = int((n1[:1]))
            if len(n1)>2:
                posz = int((n1[1:]))
            else:
                posz= 0
        else:
            posy = 0
            posz=0

        if len(str)<=1:
            n1 =  str[1:]
        else:
            n1 = name

        val ={'name': n1,
              'usage': 'internal',
              'import_name': name,
              'location_id': pasillo_id,
              'posx': posx,
              'posy': posy,
              'posz': posz}

        loc = self.env['stock.location'].create(val)
        LOCATION_IDS.append(loc)
        _logger.info('SE HA CREADO LA UBIACIÓN: {}'.format(loc.display_name))

        return loc.id




    def get_location_id(self, location):
        sl_dom = ['|', ('name', '=', location), ('import_name', '=', location)]
        location_id = self.env['stock.location'].search_read(sl_dom, ['id'], limit=1)
        if not location_id:
            location_id = self.get_loc_vals(location)
        else:
            location_id = location_id[0]['id']
        return location_id

    def new_inventory(self):
        vals= {'name': self.name,
               'filter': 'partial',
               'location_id': self.location_id.id}
        inv = self.env['stock.inventory'].create(vals)
        return inv

    def import_products(self):
        self.ensure_one()
        _logger.info(_('STARTING PRODUCT IMPORTATION'))

        # get the first worksheet
        file = base64.b64decode(self.file)
        book = xlrd.open_workbook(file_contents=file)
        sh = book.sheet_by_index(0)
        created_product_ids = []
        idx = self.start_line
        location_ids = {}
        inv = self.new_inventory()
        inv.action_start()
        line_ids = self.env['stock.inventory.line']
        if self.end_line > 0:
            end_line = self.end_line
        else:
            end_line = sh.nrows

        for nline in range(min(1, idx), end_line):
            idx += 1
            row = sh.row_values(nline)
            row_vals = self._parse_row_vals(row, idx)
            if not row_vals['default_code']:
                break
            default_code = row_vals['default_code']
            pp_dom = [('default_code', '=', default_code)]
            product_id = self.env['product.product'].search(pp_dom, limit=1)
            stock = float(row_vals['stock'])
            if not product_id:
                _logger.info ('----------------\nNO SE HA ENCONTRADO EL ARTICULO: {} en la línea {}'.format(default_code, idx))
            import_loc_name = ""
            #row_vals['ubicacion_1'] + '-' +row_vals['ubicacion_2'] + '-' +row_vals['ubicacion_3'] + '-' +row_vals['ubicacion_4'] + '-' +row_vals['ubicacion_5'] + '-' +row_vals['ubicacion_6'] + '-' +row_vals['ubicacion_7']
            for ubic in range(1,7):
                name = 'ubicacion_{}'.format(ubic)
                if row_vals[name]:
                    if import_loc_name:
                        import_loc_name = '{}-{}'.format(import_loc_name, row_vals[name])
                    else:
                        import_loc_name = row_vals[name]
                palet = row_vals[name]
                if palet[:1] == 'P':
                    ## Es palet
                    new_pack_vals = {'name': palet,
                                     'import_product_id': product_id.id,
                                     'import_name': 'Palet: {} - {}'.format(palet, product_id.display_name)}
                    new_pack = self.env['stock.quant.package'].create(new_pack_vals)
                    _logger.info('Nuevo paquete: {}'.format(new_pack_vals['import_name']))

            location = row_vals['ubicacion_1'].strip()

            location_id = self.get_location_id(location)

            new_line = {'product_id': product_id.id,
                        'location_id': location_id,
                        'inventory_id': inv.id,
                        'product_qty': stock}
            new_line = line_ids.create(new_line)
            p_vals = {'property_stock_location': location_id,
                      'import_location_str': import_loc_name}
            product_id.write(p_vals)
            _logger.info(
                '{} - {} en {}: Stock {} Uds'.
                    format(idx,
                           product_id.display_name,
                           self.env['stock.location'].browse(location_id).display_name,
                           stock,
                           ))


        if LOCATION_IDS:
            str = 'Ubiciones creadas: \n'
            for loc in LOCATION_IDS:
                str = '{}{}\n'.format(str, loc.display_name)
            _logger.info(str)




        return self.action_view(inv)

    def action_view(self, inv):
        self.ensure_one()
        action = self.env.ref(
            'stock.action_inventory_form').read()[0]
        action['res_id'] = inv.id
        action['context'] = ''
        return action
