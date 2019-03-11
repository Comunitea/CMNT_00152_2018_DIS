# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.osv import expression


class ProductCustomerValue(models.Model):

    _name = 'product.customer.value'

    @api.multi
    def _name_get(self):
        res = []
        partner_id = self._context.get('customer_partner_id', False)
        for val in self:
            res.append((val.id, val.default_code))
        return res


    product_id = fields.Many2one('product.product', string="Related product", required=True, ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('customer', '=', True)])
    default_code = fields.Char('Default code')
    description = fields.Char('Description')

class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    def _name_get(self):
        result = []
        partner_id = self._context.get('customer_partner_id', False)
        if partner_id:
            own_product_codes = self.env['res.partner'].search_read([('id', '=', partner_id)], ['own_product_codes'], limit=1)
            own_product_code = own_product_codes and own_product_codes[0]['own_product_codes']
            if own_product_code:
                for product in self:
                    domain = [('product_id', '=', product.id), ('partner_id', '=', partner_id)]
                    customer_vals = self.env['product.customer.value']
                    val = customer_vals.search_read(domain, ['default_code','description'])
                    if val:
                        name = '[%s] %s' % (val[0]['default_code'], val[0]['description'])
                        result.append((product.id, name))
                        self -= product
        old_res = self._name_get()
        return result.append(old_res)

    @api.multi
    def _get_customer_values(self):
        partner_id = self._context.get('customer_partner_id', False)
        if partner_id:
            for product in self:
                domain = [('product_id', '=', product.id), ('partner_id', '=', partner_id)]
                customer_vals = self.env['product.customer.value']
                val = customer_vals.search_read(domain, ['default_code','description'])
                if val:
                    product.write({
                            'customer_default_code': val[0]['default_code'],
                            'customer_name': val[0]['description']})

    customer_default_code = fields.Char('Customer code', compute=_get_customer_values)
    customer_name = fields.Char('Customer description', compute=_get_customer_values)
    action_view_customer_refs = fields.One2many('product.customer.value', 'product_id', 'Customer vals')
    partner_customer_value_id = fields.Many2one('res.partner', 'Customer values', store=False)

    def action_view_customer_refs(self):
        routes = self.mapped('action_view_customer_refs')



        action = self.env.ref('stock.action_routes_form').read()[0]
        action['domain'] = [('id', 'in', routes.ids)]
        return action