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

PASILLO = {'A': 1 ,'B': 2 ,'C': 3 ,'D': 4 ,'E': 5 ,'F': 6 ,'G': 7, 'H': 8 ,
           'I': 9 ,'J': 10 ,'K': 11 ,'L': 12 ,'M': 13 ,'N': 14, 'O': 15, 'P': 16,
           'Q': 17, 'R': 18, 'S': 19, 'T': 20, 'U': 21, 'V': 21, 'X': 22, 'Y': 23, 'Z': 24,
           'CIT': 40 ,'ZA': 50 ,'ZB': 51 ,'BE': 60 ,'EM': 70,'EXPOS': 80}
LOCATION_IDS = []

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    @api.multi
    def get_product_ids(self):
        for pack in self:
            domain =[('package_id', '=', pack.id)]
            quant_ids = self.env['stock.quant'].search(domain)
            pack.product_ids = quant_ids.mapped('product_id')



    import_name = fields.Char('Import name')
    product_ids = fields.One2many('product.product', string='Producto orig.', compute=get_product_ids)


class StockLocation (models.Model):

    _inherit ='stock.location'

    import_name = fields.Char(string="Ubicación importada")
    floor = fields.Integer(string="Piso", default=-1)
    building = fields.Integer(string="Nave", default=-1)
    inverse_order = fields.Boolean('Prioridad inversa', help='Si está marcado el orden de la prioridad es inverso', default=False)
    is_pos_x = fields.Boolean('Pasillo', default=False)

    _sql_constraints = [
        ('import_name_uniq', 'unique (import_name)', 'The import_name name must be unique !')
    ]

    @api.multi
    def set_removal_priority(self):

        for location in self.filtered(lambda x:x.usage == 'internal'):
            try:
                pasillo = False
                parent = location
                while parent and not pasillo:
                    if parent.is_pos_x:
                        pasillo = parent
                    parent = parent.location_id
                if parent:
                    posx = min(99, pasillo.posx)
                    posy = location.posy if not pasillo.inverse_order else 99-location.posy
                    posz = location.posz
                    location.removal_priority = int('%02d%02d%02d' %(posx, posy, posz))
                    _logger.info('Actualizando RP {}: {}'.format(location.display_name, location.removal_priority))
                else:
                    _logger.info('NO se ha encontrado un pasillo para  {}'.format(location.display_name))
            except:
                _logger.info('ERROR Actualizando RP {}'.format(location.display_name))


    @api.multi
    def set_barcode(self):
        for location in self.filtered(lambda x:x.usage == 'internal'):
            try:
                if location.floor != -1 and location.building != -1 and not location.is_pos_x:
                    location.barcode = '%01d%01d%02d%02d%02d'%(location.building, location.floor, location.posx, location.posy, location.posz)
                    _logger.info('Actualizando CDB {}: {}'.format(location.display_name, location.barcode))
            except:
                _logger.info('ERROR Actualizando CDB {}'.format(location.display_name))

    @api.multi
    def set_parent_vals(self):
        for loc in self:
            view = False
            location = loc
            while location and not view:
                print('Ubicación {} y padre {}'.format(location.name, location.location_id.name))
                if location.usage == 'view' and location.posx == 0:
                    view = location
                location = location.location_id
            loc.building = view.building
            loc.floor = view.floor


class ProductTemplate (models.Model):

    _inherit ='product.template'

    import_location_str = fields.Char(string="Ubicación importada")

class ProductProduct(models.Model):

    _inherit ='product.product'

    def create_putaway_imported(self, location, location_id):
        strategic_id = location.putaway_strategy_id
        if not strategic_id:
            raise ValueError ('La ubicación {} not tiene estrategia de traslado'.format(location.name))

        sfps = self.env['stock.fixed.putaway.strat']
        val = {'sequence': 1,
               'putaway_id': strategic_id.id,
               'product_id': self.id,
               'fixed_location_id': location_id}

        sfps.create(val)

class ProductImportWzd(models.TransientModel):

    _name = 'product.import.wzd'

    @api.multi
    def get_default(self):
        return self.env['stock.location'].browse(12)

    name = fields.Char('Importation name', required=True)
    file = fields.Binary(string='File', required=True)
    start_line = fields.Integer("Desde linea")
    end_line = fields.Integer("Hasta linea")
    location_id = fields.Many2one('stock.location', 'Ubicación del ajuste', default = get_default)
    filename = fields.Char(string='Filename')
    only_create_locations = fields.Boolean('Solo ubicaciones')

    @api.onchange('file')
    def onchange_filename(self):
        if not self.name and self.filename:
            self.name = self.filename and self.filename.split('.')[0]

    def _parse_rows(self):
        pass

    def _parse_row_vals(self, row, idx):
        res = {
            'default_code': str(row[0]).upper(),
            'nombre_articulo': str(row[1]),
            'ubicacion_1': str(row[2]).upper(),
            'ubicacion_2': str(row[3]).upper(),
            'ubicacion_3': str(row[4]).upper(),
            'ubicacion_4': str(row[5]).upper(),
            'ubicacion_5': str(row[6]).upper(),
            'ubicacion_6': str(row[7]).upper(),
            'ubicacion_7': str(row[8]).upper(),
            'stock': float(row[9]) or 0.0,
            #'cost': float(row[10]) or 0.0,
        }
        # Check mandatory values setted
        if not row[0]:
            raise UserError(
                _('Missing Code in row %s ') % str(idx))

        return res

    def get_pasillo_vals(self, pasillo, planta_id):

        planta = self.env['stock.location'].browse(planta_id)
        import_name =  "{}.{}".format(planta.name, pasillo)
        pl_dom = [('import_name', '=', import_name)]
        pasillo_id = self.env['stock.location'].search_read(pl_dom, ['id'], limit=1)
        posx = int(PASILLO.get(pasillo, 0))
        if not pasillo_id:
            pasillo_vals = {'name': pasillo,
                            'posx': posx,
                            'import_name': import_name,
                            'location_id': planta_id,
                            'is_pos_x': True,
                            'usage': 'internal'}

            pasillo_id = self.env['stock.location'].create(pasillo_vals)
            view = False
            location = pasillo_id
            while location and not view:
                print ('Ubicación {} y padre {}'.format(location.name, location.location_id.name))
                if location.usage == 'view' and location.posx == 0:
                    view = location
                location = location.location_id

            pasillo_id.building = view.building
            pasillo_id.floor = view.floor

            LOCATION_IDS.append(pasillo_id)
            _logger.info('SE HA CREADO EL PASILLO: {}'.format(pasillo_id.display_name))
            self._create_xml_id('stock_location', pasillo_id.location_id.name + '_' + pasillo_id.name, pasillo_id.id, 'stock.location')
            pasillo_id = pasillo_id.id
        else:
            pasillo_id = pasillo_id[0]['id']
        return pasillo_id

    def  get_loc_vals(self, import_name):

        def sin_numeros(s):
            numeros = "1234567890"
            s_sin_numeros = ""
            for letra in s:
                if letra not in numeros:
                    s_sin_numeros += letra
            return s_sin_numeros

        name = import_name

        ##ES PLANTA 1
        if import_name[:1] == '1':
            nombre_sin_pasillo = import_name[1:]
            domain = [('name', '=', 'Planta 1')]
            planta_id = self.env['stock.location'].search_read(domain, ['id'], limit=1)[0]['id']
        ##ES PALET
        elif import_name[:1] == 'P':
            ##devuelvo la ubiación de palets
            domain = [('name', '=', 'Palets')]
            return self.env['stock.location'].search_read(domain, ['id'], limit=1)[0]['id']
        #ES PLANTA 0
        else:
            nombre_sin_pasillo = import_name
            domain = [('name', '=', 'Planta 0')]
            planta_id = self.env['stock.location'].search_read(domain, ['id'], limit=1)[0]['id']

        ## el pasillo siempre es son letras
        pasillo = sin_numeros(nombre_sin_pasillo)
        pasillo_id = self.get_pasillo_vals(pasillo, planta_id)
        ##sa co el pos x de los pasillos
        posx = int(PASILLO.get(pasillo, 0))
        ## n1 debe ser el nombre sin el pasillo y sin la planta -> posy y posz
        n1 = nombre_sin_pasillo.replace(pasillo, '')

        if len(n1) > 0:
            posy = int((n1[:1]))
            if len(n1) > 1:
                posz = int((n1[1:]))
            else:
                posz= 0
        else:
            posy = 0
            posz = 0

        if len(import_name) <= 1:
            n1 = import_name[1:]
        else:
            n1 = name

        val ={'name': name,
              'usage': 'internal',
              'import_name': import_name,
              'location_id': pasillo_id,
              'is_pos_x': False,
              'posx': posx,
              'posy': posy,
              'posz': posz}
        _logger.info('CREANDO LA UBIACIÓN: {}: {}'.format(name, n1))
        loc = self.env['stock.location'].create(val)

        view = False
        location = loc
        while location and not view:
            print ('Ubicación {} y padre {}'.format(location.name, location.location_id.name))
            if location.usage == 'view' and location.posx == 0:
                view = location
            location = location.location_id

        loc.building = view.building
        loc.floor = view.floor
        self._create_xml_id('stock_location', loc.location_id.name + '_' + loc.name, loc.id, 'stock.location')

        LOCATION_IDS.append(loc)
        _logger.info('SE HA CREADO LA UBIACIÓN: {}'.format(loc.display_name))
        return loc.id



    def get_location_id(self, import_name):
        if not import_name:
            domain = [('name', '=', 'Generico')]
            location_id = self.env['stock.location'].search_read(domain, ['id'], limit=1)
            return location_id

        sl_dom = [('usage', '=', 'internal'), ('import_name', '=', import_name)]
        location_id = self.env['stock.location'].search_read(sl_dom, ['id'], limit=1)
        if not location_id:
            location_id = self.get_loc_vals(import_name)
        else:
            location_id = location_id[0]['id']
        return location_id

    def new_inventory(self):
        vals= {'name': self.name,
               'filter': 'partial',
               'location_id': self.location_id.id}
        inv = self.env['stock.inventory'].create(vals)
        return inv

    def _create_xml_id(self, modulo, xml_id, res_id, model):
        sql = "delete from  ir_model_data where model='%s' and name='%s'" % (model, xml_id)
        _logger.info('SE ha ejecutado\n: {}'.format(sql))
        self._cr.execute(sql)
        sql= "INSERT INTO ir_model_data (module, name, res_id, model) VALUES ('%s', '%s', %s, '%s')" %(modulo, xml_id, res_id, model)
        _logger.info('SE ha ejecutado\n: {}'.format(sql))
        self._cr.execute(sql)
        return True

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
        location_palet = self.env['stock.location'].search([('name', '=', 'Palets')])
        if not self.only_create_locations:
            inv = self.new_inventory()
            inv.action_start()
            line_ids = self.env['stock.inventory.line']
        if self.end_line > 0:
            end_line = self.end_line
        else:
            end_line = sh.nrows

        header = sh.row_values(0)


        for nline in range(max(1, idx), end_line):
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
                    new_pack = self.env['stock.quant.package'].search([('name', '=', palet)])
                    if not new_pack:
                        ## Es palet
                        new_pack_vals = {'name': palet,
                                         'import_name': 'Palet: {}'.format(palet)}
                        new_pack = self.env['stock.quant.package'].create(new_pack_vals)
                        self._create_xml_id('sqp', new_pack.name, new_pack.id, 'stock.quant.package')
                        _logger.info('Nuevo paquete: {}'.format(new_pack_vals['import_name']))

                    new_quant_val = {'product_id': product_id.id,
                                     'location_id': location_palet.id,
                                     'quantity': 0,
                                     'product_uom_id': product_id.uom_id.id,
                                     'package_id': new_pack.id
                                     }
                    new_quant = self.env['stock.quant'].sudo().create(new_quant_val)

            location = row_vals['ubicacion_1'].strip()
            location_id = self.get_location_id(location)
            if not self.only_create_locations and stock > 0:
                new_line_vals = {'product_id': product_id.id,
                                'location_id': location_id,
                                'inventory_id': inv.id,
                                'product_qty': stock}
                new_line = line_ids.create(new_line_vals)


            p_vals = {'import_location_str': import_loc_name}

            if location[:1] == 'P':
                location_id = location_palet.id

            product_id.create_putaway_imported(self.location_id, location_id)


            product_id.write(p_vals)
            _logger.info(
                '{} - {} en {}: Stock {} Uds'.
                    format(idx,
                           product_id.display_name,
                           self.env['stock.location'].browse(location_id).display_name,
                           stock,
                           ))


        if LOCATION_IDS:
            if False:
                for loc_id in LOCATION_IDS:
                    try:
                        loc_id.set_barcode()
                        loc_id.set_removal_priority()
                    except:
                        _logger.info('Error actualizando datos de ubicación" LA UBIACIÓN: {}'.format(name))
            str = 'Ubiciones creadas: \n'
            for loc in LOCATION_IDS:
                str = '{}{}\n'.format(str, loc.display_name)
            _logger.info(str)
        if self.only_create_locations:
            return self.action_view_location()
        else:
            return self.action_view(inv)

    def action_view_location(self):
        self.ensure_one()
        action = self.env.ref(
            'stock.action_location_form').read()[0]
        action['domain'] = [('import_name', '!=', '')]
        action['context'] = ''
        return action
    def action_view(self, inv):
        self.ensure_one()
        action = self.env.ref(
            'stock.action_inventory_form').read()[0]
        action['res_id'] = inv.id
        action['context'] = ''
        return action
