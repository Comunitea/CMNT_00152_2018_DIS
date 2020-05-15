# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResUsers(models.Model):

    _inherit = "res.users"

    def _create_user_from_template(self, values):
        print(values.get('partner_id', False))
        if not values.get('partner_id', False):
            website = self.env['website'].get_current_website()
            web_default_pricelist = website.get_pricelist_available()[0]
            values['property_product_pricelist'] = web_default_pricelist.id
            #FORZAMOS QUE SE USE AL CREAR UN NUEVO USUARIO LA TARIFA WEB POR DEFECTO    
        return super()._create_user_from_template(values)
    