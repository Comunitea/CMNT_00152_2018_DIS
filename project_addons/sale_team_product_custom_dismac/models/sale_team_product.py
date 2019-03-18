# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api, _
from traceback import format_exception
from odoo.exceptions import UserError

class SaleTeamProductData(models.Model):
    _name = "sale.team.product"

    product_tmpl_id = fields.Many2one('product.template', string='product', required=True, ondelete="cascade")
    team_id = fields.Many2one(
        'crm.team',
        string='Sales Team', required=True, ondelete="cascade"
    )    
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used as image for the product, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of the product. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved, "
             "only when the image exceeds one of those sizes. Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of the product. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    description = fields.Text(
        'Description', translate=True,
        help="A precise description of the Product, used only for internal information purposes.")
    _sql_constraints = [
        ('product_sale_team_uniq', 'unique(product_tmpl_id, team_id)',
         'There is already a customization for this product with the team sale you selected, check it out.')
    ]

    @api.multi
    @api.constrains('description', 'image')
    def check_if_both_empty(self):
        for var in self:
            if not var.description and not var.image:
                raise UserError(
                    _("Description and image fields are both empty, you need to define atleast one of them."))

    @api.multi
    def _image_get(self):
        self.ensure_one()
        return self.image or False
        

    @api.multi
    def _description_get(self):
        self.ensure_one()
        return self.description or ''
        
                        