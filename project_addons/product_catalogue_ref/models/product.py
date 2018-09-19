# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    @api.depends('product_variant_ids', 'product_variant_ids.catalogue_code')
    def _compute_catalogue_code(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.catalogue_code = template.product_variant_ids.catalogue_code
        for template in (self - unique_variants):
            template.catalogue_code = ''

    @api.one
    def _set_catalogue_code(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.catalogue_code = self.catalogue_code

    @api.multi
    @api.depends('barcode')
    def _get_ean13_char(self):
        for product in self:
            product.ean13_str = product.barcode

    catalogue_code = fields.Char(
        'Catalogue Reference', compute='_compute_catalogue_code',
        inverse='_set_default_code', store=True)

    ean13_str = fields.Char('Ean13 char', compute="_get_ean13_char", store=True)

    @api.model
    def create(self, vals):
        template = super(ProductTemplate, self).create(vals)

        related_vals = {}
        if vals.get('catalogue_code'):
            related_vals['catalogue_code'] = vals['catalogue_code']
        if related_vals:
            template.write(related_vals)
        return template

class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    @api.depends('ean13_ids')
    def _get_ean13_char(self):
        for product in self:
            ean13_char = product.barcode
            for barcode in product.ean13_ids:
                ean13_char = '{}.{}'.format(ean13_char, barcode.name)
            product.ean13_str = ean13_char

    catalogue_code = fields.Char('Catalogue Reference', index=True)
    ean13_str = fields.Char('Ean13 char', compute="_get_ean13_char", store=True)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []

        if name and operator in ['=', 'ilike', '=ilike', 'like', '=like']:
            args = args + ['|', ('catalogue_code', '=', name), ('ean13_ids.name', 'in', name)]
        return super(ProductProduct, self).name_search(name=name, args=args, operator=operator, limit=limit)
