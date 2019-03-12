# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    @api.onchange('team_id')
    def team_id_change(self): 
        for order in self.filtered(lambda x: x.team_id):
            order.order_line.update_product_sale_team(order.team_id.id)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def update_product_sale_team(self, team_id):
        for line in self:
            domain = [('team_id', '=', team_id), ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)]
            value = self.env['sale.team.product'].search(domain, limit=1)
            if value:
                name = '[{}] {}'.format(line.product_id.default_code, value.description or line.product_id.description_sale)
                line.name = name
        return

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):        
        res = super().product_id_change()
        if self.order_id.team_id and self.product_id:
            self.update_product_sale_team(self.order_id.team_id.id)
        return res

    