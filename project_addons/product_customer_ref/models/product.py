# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.osv import expression


class ProductCustomerValue(models.Model):

    _name = 'product.customer.value'
    _rec_name = 'default_code'

    @api.multi
    def name_get(self):
        res = []
        for val in self:
            name = '[%s] %s' % (val.default_code, val.description)
            res.append((val.id, name))
        return res

    product_id = fields.Many2one(
        'product.product', string="Related product",
        required=True, ondelete="cascade")
    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        domain=[('customer', '=', True)], required=True)
    default_code = fields.Char('Default code')
    description = fields.Char('Description')


class ProductProduct(models.Model):

    _inherit = 'product.product'

    def get_context_partner(self, context):
        p_id = context.get('partner_id', False)
        partner_id = False
        if isinstance(p_id, int):
            partner_id = self.env['res.partner'].browse(p_id)
        elif p_id:
            partner_id = self.env['res.partner'].search(
                [('name', '=', p_id)], limit=1)

        return partner_id

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        partner_id = self.get_context_partner(self._context)
        if partner_id and partner_id.own_product_codes:
            domain = [
                ('partner_id', '=', partner_id.id),
                ('default_code', operator, name)]
            customer_vals = self.env['product.customer.value']
            ids = customer_vals.search(domain).mapped('product_id').ids
            if ids:
                args = expression.AND([args, [('id', 'in', ids)]])
        return super().name_search(
            name=name, args=args, operator=operator, limit=limit)

    @api.multi
    def name_get(self):
        result = []
        partner_id = self.get_context_partner(self._context)
        if partner_id and partner_id.own_product_codes:
            for product in self:
                domain = [
                    ('product_id', '=', product.id),
                    ('partner_id', '=', partner_id.id)]
                customer_vals = self.env['product.customer.value']
                val = customer_vals.search(domain)
                if val:
                    name = '[%s] %s' % (val.default_code, val.description)
                    result.append((product.id, name))
                    self -= product
        res = super(ProductProduct, self).name_get()
        if result:
            res += result
        return res

    @api.multi
    def _get_customer_values(self):
        partner_id = self.get_context_partner(self._context)
        if partner_id:
            for product in self:
                domain = [
                    ('product_id', '=', product.id),
                    ('partner_id', '=', partner_id.id)]
                customer_vals = self.env['product.customer.value'].search(
                    domain, limit=1)
                if customer_vals:
                    product.customer_default_code = customer_vals.default_code
                    product.customer_name = customer_vals.description
                else:
                    product.customer_default_code = self._context.get(
                        'customer_partner_id', 'Sin codigo')

    customer_default_code = fields.Char(
        'Customer code', compute=_get_customer_values)
    customer_name = fields.Char(
        'Customer description', compute=_get_customer_values)
    product_customer_value_ids = fields.One2many(
        'product.customer.value', 'product_id', 'Customer vals')
    product_customer_value_id = fields.Many2one(
        'res.partner', 'Customer values', store=False)

    def action_view_customer_refs(self):
        routes = self.mapped('product_customer_value_ids')
        action = self.env.ref(
            'product_customer_ref.action_customer_refs_tree').read()[0]
        action['domain'] = [('id', 'in', routes.ids)]
        action['context'] = {
            'hide_product_column': True,
            'default_product_id': self.id,
            'default_default_code': self.default_code,
            'default_description': self.description_sale}
        return action
