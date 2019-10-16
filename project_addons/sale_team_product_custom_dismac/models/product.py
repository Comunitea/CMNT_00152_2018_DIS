# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sale_team_product_ids = fields.One2many(
        "sale.team.product", "product_tmpl_id", String="Sale team product data"
    )
    image_team = fields.Binary("Image (team)", compute="_team_values_get")
    description_team = fields.Text(
        "Description sale (team)", compute="_team_values_get"
    )

    @api.multi
    def _team_values_get(self):
        result = []
        team_id = self._context.get("team_id", False)
        sale_team_vals = self.env["sale.team.product"]
        fields = ["image", "description"]
        if team_id:
            for template in self:
                domain = [
                    ("product_tmpl_id", "=", template.id),
                    ("team_id", "=", team_id),
                ]
                val = sale_team_vals.search_read(domain, fields)
                template.image_team = val and val[0]["image"] or template.image
                template.description_team = (
                    val and val[0]["description"] or template.description_sale
                )
