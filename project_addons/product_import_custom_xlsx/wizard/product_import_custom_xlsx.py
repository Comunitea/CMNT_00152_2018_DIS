# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import xlrd
import base64

import logging
_logger = logging.getLogger(__name__)
START_STOCK = 11
CATEG_IDS = {
    'C': '2.- CON: CONSUMIBLE ORIGINAL', 
    'P': '1.- PAP: PAPELERÍA',
    'M': '3.- MOB: MOBILIARIO',
    'I': '4.- INF: INFORMÁTICA'
}
class ProductImportCustomXlsx(models.TransientModel):
    _name = "product.import.custom.xlsx"

    @api.model
    def get_default_location(self):
        domain = [('name', '=', 'Nave 2')]
        return self.env['stock.location'].search(domain, limit=1)

    @api.model
    def get_default_partner(self):
        domain = [('vat', '=', 'ESB80441306')]
        return self.env['res.partner'].search(domain, limit=1)
    
    @api.model
    def get_default_tag_id(self):
        domain = [('name', '=', 'ADTD')]
        return self.env['product.template.tag'].search(domain, limit=1)

    @api.model
    def get_default_cost_ratio(self):
        domain = [('name', '=', 'B.- MATERIAL OFICINA')]
        return self.env['product.price.ratio'].search(domain, limit=1)

    name = fields.Char('Importation name', required=True)
    file = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Filename')
    check_ean = fields.Boolean('Check EAN 13', default=True)
    check_qties = fields.Boolean('Check Qties', default=True)
    only_products = fields.Boolean('Solo artículos', default=False)
    location_id = fields.Many2one('stock.location', string = 'Location', default=get_default_location)
    categ_ids = fields.Many2many('product.category')
    supplier_id = fields.Many2one('res.partner', string='Proveedor', default=get_default_partner)
    cost_ratio_id = fields.Many2one('product.price.ratio', string="Coeficiente de referencia", default=get_default_cost_ratio)
    tag_id = fields.Many2one('product.template.tag', string="Etiqueta",  default=get_default_tag_id)
    validate_inventory = fields.Boolean('Validación de inventario', default=True)
    
    @api.onchange('file')
    def onchange_filename(self):
        if not self.name and self.filename:
            self.name = self.filename and self.filename.split('.')[0]

    def _create_xml_id(self, product_id):
        sql = "INSERT INTO ir_model_data (module, name, res_id, model) VALUES ('%s', '%s', %s, '%s'), ('%s', '%s', %s, '%s')" % ('PP', product_id.default_code, product_id.id, 'product.product', 'PT', product_id.default_code, product_id.product_tmpl_id.id, 'product.template')
        self._cr.execute(sql)
    
    def _create_location_xml_id(self, palet_id):
        sql = "INSERT INTO ir_model_data (module, name, res_id, model) VALUES ('%s', '%s', %s, '%s')" % ('SL', palet_id.name, palet_id.id, 'stock.location')
        self._cr.execute(sql)

    def cad_to_number(self, cad, return_type=str):

        if return_type == str:
            if isinstance(cad, str):
                cad = cad.strip()
                return cad
            elif isinstance(cad, float):
                cad = int(cad)
            try:
                return '%s' % cad
            except:
                return ''

        elif return_type == int:
            if isinstance(cad, str):
                cad = cad.strip()
            if not cad:
                return 0
            try:
                return int(cad)
            except:
                return 0


        elif return_type == float:
            if isinstance(cad, str):
                cad = cad.strip()
            if not cad:
                return 0
            try:
                return float(cad)
            except:
                return 0
        return False

    def _parse_row_vals(self, row, categ_dict):
    
        cost_ratio = str(row[8]).strip()
        barcode = self.cad_to_number(row[1])
        default_code = str(row[0]).strip()
        if self.check_ean and barcode and len(barcode) != 13:
            error_msg = 'Error en EAN en %s : %s' %(default_code, barcode)
            raise ValidationError (error_msg)
        
        res = {
            'default_code': default_code,
            'categ_id': categ_dict[str(row[2])],
            'name': str(row[3]).strip(),
            'standard_price': str(row[4]),
            #'supplier_id': str(row[5]),
            #'reaprovisionamiento_max': str(row[6]),
            #'reaprovisionamiento_minimo': str(row[7]),
            'cost_ratio_id': self.cost_ratio_id.id,
            }
        if len(barcode)==13:
            res['barcode'] = barcode
        if not self.supplier_id:
            domain = [('name', '=', str(row[5]))]
            self.supplier_id = self.env['res.partner'].search(domain, limit=1)
        
        return res

    def _get_row_product(self, product_values, faltan = 0):
        domain = [('default_code', '=', product_values['default_code']), '|', ('active', '=', False), ('active', '=', True)]
        product_id = self.env['product.product'].search(domain)
        default_values = {
                'active': True,
                'type': 'product',
                'sale_ok': True,
                'purchase_ok': True,
                #'sale_line_warn': 'warning',
                #'sale_line_warn_msg': 'Este articulo debería actualizarse',
                'description_pickingin': 'Archivo: %s' % self.name

            }
        product_values.update(default_values)
        if product_id:
            _logger.info ("%s: Encontrado %s" % (faltan, product_id.default_code))
            if not product_id.active:
                _logger.info ("    Desactivado > Actualizando %s" % product_id.default_code)
                product_id.write(product_values)
            create=False
        else:
            if self.tag_id:
                product_values.update(tag_ids=[(4,self.tag_id.id)])
            product_id = product_id.create(product_values)
            #self._create_xml_id(product_id)
            _logger.info ("%s: Producto creado: %s" % (faltan, product_id.default_code))
            self.add_suplier_info(product_id)
            create = True
        return product_id, create

    def update_CATEG_IDS(self):
        categ_ids = self.env['product.category']
        categ_dict = {}
        for key in CATEG_IDS.keys():
            domain = [('name', '=', CATEG_IDS[key])]
            categ_id = categ_ids.search(domain, limit = 1)
            categ_dict[key] = categ_id.id

        return categ_dict

    def add_suplier_info (self, product_id):
        supplier_id = self.supplier_id
        vals = {'name': supplier_id.id, 'product_tmpl_id': product_id.product_tmpl_id.id}

        domain = [('name', '=', supplier_id.id), ('product_tmpl_id', '=', product_id.product_tmpl_id.id)]
        supplier_id = self.env['product.supplierinfo'].search(domain)
        if not supplier_id:
            supplier_id = self.env['product.supplierinfo'].create(vals)

    def _get_stock_inventory(self, palet):
        domain = [('name', '=', palet), ('location_id', '=', self.location_id.id)]
        palet_id = self.env['stock.location'].search(domain)
        create=False
        if not palet_id:
            palet_vals = {'name': palet, 'location_id': self.location_id.id, 'floor': 0, 'usage': 'internal', 'building': 10,  'removal_priority': 999 }
            palet_id = self.env['stock.location'].create(palet_vals)
            create=True
            #self._create_location_xml_id(palet_id)
        inv_name = '%s : %s' %(self.name, palet_id.name)
        domain = [('name', '=', inv_name), ('state', '=', 'confirm')]
        inventory_id = self.env['stock.inventory'].search(domain)
        if not inventory_id:
            vals = {
                'name': inv_name,
                'location_id': palet_id.id,
                'filter': 'partial'
            }
            inventory_id = self.env['stock.inventory'].create(vals)
            inventory_id.action_start()
            inventory_id.action_reset_product_qty()

        return inventory_id, palet_id, create

    
    def import_products(self):
        self.ensure_one()
        _logger.info(_('STARTING PRODUCT IMPORTATION'))
        # get the first worksheet
        file = base64.b64decode(self.file)
        book = xlrd.open_workbook(file_contents=file)
        sh = book.sheet_by_index(0)
        
        _logger.info ("Calculando categorias %s" % CATEG_IDS)
        categ_dict = self.update_CATEG_IDS()
        _logger.info ("                   >> %s" % categ_dict)
        idx = 2
        nrows = sh.nrows
        #StockInventory= self._get_stock_inventory()
        max_lines = 100
        product_ids = {}
        default_code = {}
        product_obj_ids = self.env['product.product']
        location_ids = self.env['stock.location']
        inventory_ids = self.env['stock.inventory']
        if self.check_ean:
            EAN_values = sh.col_values(1, 2)
            lineas = []
            for line in range(2, len(EAN_values)):
                barcode = self.cad_to_number(EAN_values[line])
                if barcode and len(barcode) != 13:
                    lineas += [line+3]
            if lineas:
                raise ValidationError ('Error de EAN en las líneas %s' % lineas)
        
        for nline in range(idx, nrows):
            if idx > max_lines :
                pass
            idx += 1
            row = sh.row_values(nline)
            product_values = self._parse_row_vals(row, categ_dict)
            product_id, create = self._get_row_product(product_values, nrows - nline)
            if create:
                product_obj_ids |= product_id
            ## ahora relleno Stock
            product_ids[nline] = product_id.id
            default_code[nline] = product_id.default_code
        
        for product_id in product_obj_ids:
            self._create_xml_id(product_id)
            product_id.generate_warehouse_order()
        if self.only_products:
            return
        palet_names = sh.row_values(1)[START_STOCK:]
        _logger.info ("STOCK: Palets %s" % palet_names)
        col_cont = START_STOCK
        
        for palet_name in palet_names:
            if col_cont > 50:
                pass
                #break
        
            inventory_id, palet_id, create = self._get_stock_inventory(palet_name)
            if create:
                location_ids |= palet_id
            inventory_ids |= inventory_id
            line_template = {'inventory_id': inventory_id.id,
                            'location_id': palet_id.id}
            
            col_values = sh.col_values(col_cont)
            col_qty = col_values[0]
            _logger.info ("  >>  Palet %s: %s Uds" % (palet_id.name, col_qty))
            idx = 2
            for nline in range(idx, nrows):
                if idx > max_lines :
                    pass
                idx += 1

                qty = self.cad_to_number(col_values[nline], int)
                if qty > 0:
                    col_qty -= qty
                    product_id = product_ids[nline]
                    line_domain = [('inventory_id', '=', inventory_id.id), ('product_id', '=', product_id)]
                    line_id = self.env['stock.inventory.line'].search(line_domain)
                    if line_id:
                        line_id.product_qty = qty
                    else:
                        line_template.update(product_id=product_id, product_qty = qty)
                        line_id = self.env['stock.inventory.line'].create(line_template)
                        line_id._onchange_product()
                    _logger.info ("         Producto %s. Cantidad %s" % (default_code[nline], qty))
            if self.check_qties and col_qty != 0:
                raise ValidationError ('La cantidad no corresponde en el palet %s'% palet_id.name)
            col_cont += 1

        
        
        for location_id in location_ids:
            self._create_location_xml_id(location_id)

        if self.validate_inventory:
            faltan = len(inventory_ids)
            _logger.info ("Validando %s inventarios"% faltan)
            for inventory_id in inventory_ids:
                if inventory_id.line_ids:
                    _logger.info ("  %s Inventario: %s" % (faltan, inventory_id.name))
                    inventory_id.action_validate()
                else:
                    _logger.info ("  %s Inventario vacío: %s" % (faltan, inventory_id.name))
                    inventory_id.unlink()
        return
    
    def delete_products(self):
        
        #sql = "INSERT INTO ir_model_data (module, name, res_id, model) VALUES ('%s', '%s', %s, '%s'), ('%s', '%s', %s, '%s')" % ('PP', product_id.default_code, product_id.id, 'product.product', 'PT', product_id.default_code, product_id.product_tmpl_id.id, 'product.template')
        #self._cr.execute(sql)
        _logger.info ("Borrado de ir_model_data")
        sql = "delete from ir_model_data where name ilike 'ADTD%' and model in ('product.product', 'product.template')"
        self._cr.execute(sql)
        _logger.info ("Borrado de stock_inventory_line")
        sql = "delete from stock_inventory_line where inventory_id in (select id from stock_inventory where name ilike 'LOD_Paletd%')"
        self._cr.execute(sql)
        _logger.info ("Borrado de stock_inventory")
        sql = "delete from stock_inventory where name ilike 'LOD_Paletd%'"
        self._cr.execute(sql)
        _logger.info ("Borrado de ir_model_data")
        sql = "delete from ir_model_data where name ilike 'PD%' and model = 'stock.location'"
        self._cr.execute(sql)
        
        _logger.info ("Borrado de product_ean13")
        sql = "delete from product_ean13"
        self._cr.execute(sql)
        _logger.info ("Borrado de product_template")
        sql = "delete from product_template where id in (select product_tmpl_id from product_product where default_code ilike 'ADTD%')"
        self._cr.execute(sql)
        _logger.info ("Borrado de product_product")
        sql = "delete from product_product where default_code ilike 'ADTD%'"
        self._cr.execute(sql)
        _logger.info ("Borrado de stock_location")
        sql = "delete from stock_location where name ilike 'PD%' and building = 10"
        self._cr.execute(sql)
    





class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def generate_warehouse_order(self):
        swo = self.env['stock.warehouse.orderpoint']
        company_id = self.env.user.company_id
        warehouse_id = self.env.user.company_id.warehouse_id
        location_id = warehouse_id.lot_stock_id
        if not warehouse_id:
            warehouse_id = self.env['stock.warehouse'].search([], limit=1)
        vals = {
            'warehouse_id': warehouse_id.id, 
            'location_id': warehouse_id.lot_stock_id.id, 
            'company_id': company_id.id,
            'product_min_qty': 0,
            'product_max_qty': 0, 
            'qty_multiple': 1}

        for product in self:
            domain = [('product_id', '=', product.id)]
            swo_id = swo.search(domain)
            if not swo_id:
                vals.update(product_id = product.id)
                print ("creando regla para %s con %s"%(product.display_name, vals))
                swo |= swo_id.create(vals)
        
        action = self.env.ref("stock.action_orderpoint_form").read()[0]
        action['context'] = {'active_ids': swo.ids}
        return action
