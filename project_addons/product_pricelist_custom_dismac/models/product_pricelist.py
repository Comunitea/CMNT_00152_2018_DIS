# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api, _

class Pricelist(models.Model):
    
    _inherit = "product.pricelist"

    is_promotion = fields.Boolean('Promotion', default=False)
    date_start = fields.Date('Start Date', help="Starting date for the pricelist item validation")
    date_end = fields.Date('End Date', help="Ending valid for the pricelist item validation")
    error_ids = fields.One2many('product.pricelist.import.error', 'import_id', 'Error items')

    @api.multi
    def show_error_list(self, context=None):
        domain = [('import_id','=',self.id)]

        return {
         'type': 'ir.actions.act_window',
         'res_model': 'product.pricelist.import.error',
         'view_type': 'form',
         'view_mode': 'tree,form',
         'view_id ref="view_product_pricelist_import_error_tree"': '',
         'target': 'current',
         'domain': domain,
        }