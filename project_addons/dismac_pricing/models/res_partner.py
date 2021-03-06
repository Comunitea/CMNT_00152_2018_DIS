# © 2019 Comunitea - Santi Argüeso <santi@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    fixed_prices = fields.Boolean(default=False, help='Considera precios fijos establecidos a este cliente , si no lo sencontrase la tarifa de precios aplicando descuentos por categoría si los hubiese')

    @api.multi
    def show_partner_prices(self, context=None):
        product_context = dict(self.env.context)
        product_context.update(
            {
                "partner": self.id,
                "pricelist": self.property_product_pricelist.id,
            }
        )
        data_obj = self.env.ref("dismac_pricing.product_partner_prices")
        return {
            "type": "ir.actions.act_window",
            "res_model": "product.product",
            "view_type": "form",
            "view_mode": "tree",
            "view_id": [data_obj.id],
            "target": "current",
            "context": product_context,
        }
