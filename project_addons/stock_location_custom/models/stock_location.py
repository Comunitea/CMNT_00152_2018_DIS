# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, models, fields, _

import logging
_logger = logging.getLogger(__name__)

# Global variable to store the new created templates
template_ids = []

PASILLO = {'A': 1 ,'B': 2 ,'C': 3 ,'D': 4 ,'E': 5 ,'F': 6 ,'G': 7, 'H': 8 ,
           'I': 9 ,'J': 10 ,'K': 11 ,'L': 12 ,'M': 13 ,'N': 14, 'O': 15, 'P': 16,
           'Q': 17, 'R': 18, 'S': 19, 'T': 20, 'U': 21, 'V': 22, 'W': 23, 'X': 24, 'Y': 25, 'Z': 26,
           'CIT': 40 ,'ZA': 50 ,'ZB': 51 ,'BE': 60 ,'EM': 70,'EXPOS': 80}
LOCATION_IDS = []
LOCATION_TYPES = [('floor', 'Planta'), ('row', 'Pasillo'), ('location', 'Estantería')]



class StockLocation (models.Model):

    _inherit ='stock.location'

    import_name = fields.Char(string="Ubicación importada")
    floor = fields.Integer(string="Piso", default=-1)
    building = fields.Integer(string="Nave", default=-1)
    inverse_order = fields.Boolean('Prioridad inversa', help='Si está marcado el orden de la prioridad es inverso', default=False)
    is_pos_x = fields.Boolean('Pasillo', default=False)
    location_type = fields.Selection(selection=LOCATION_TYPES, string="Estructura")

    _sql_constraints = [
        ('import_name_uniq', 'unique (import_name)', 'The import_name name must be unique !')
    ]

    @api.multi
    def compute_location_type(self):
        for location in self:
            if location.is_pos_x:
                location.location_type = 'row'
            elif location.location_id.is_pos_x:
                location.location_type = 'location'
            elif location.building:
                location.location_type = 'floor'
            else:
                location.location_type = False


    def get_pasillo(self):
        location_id = self
        pasillo = self.is_pos_x
        while location_id and not pasillo:
            location_id = location_id.location_id
            pasillo = location_id.is_pos_x
        return location_id


    @api.multi
    def set_removal_priority(self):
        loc_ids = self#.filtered(lambda x:x.usage == 'internal')
        tot = len(self | self.mapped('child_ids') | self.mapped('child_ids').mapped('child_ids'))
        cont=0
        for location in loc_ids:
            cont+=1
            pasillo = location.get_pasillo()
            if pasillo:
                planta = pasillo.location_id
                location.posx = pasillo.posx
                pos = planta.floor
                nave = planta.building
                posx = min(99, pasillo.posx)
                posy = location.posy if not pasillo.inverse_order else 99-location.posy

            else:
                nave = max(location.building, 0)
                pos = max(location.floor, 0)
                posx = location.posx
                posy = location.posy


            location.removal_priority = int('%01d%01d%02d%02d%02d' %(nave, pos, posx, posy, location.posz))
            barcode = '%01d%01d%02d%02d%02d' % (nave, pos, posx, location.posy, location.posz)
            _logger.info(
                'Actualizando RP {}: Prioridad: {} CDB: {}  ({} de {})'.format(location.display_name, location.removal_priority, barcode, cont, tot))
            loc = self.search([('barcode', '=', barcode)])
            for l in loc:
                l.barcode = '.%07d'%l.id
            location.barcode = barcode



            ## además tengo que buscar y actualizar las hijas.
            location.compute_location_type()
            location.search([('location_id', '=', location.id)]).set_removal_priority()

    @api.multi
    def set_barcode(self):
        return self.set_removal_priority()