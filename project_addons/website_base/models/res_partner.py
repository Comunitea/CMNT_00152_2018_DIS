# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartnerAccess(models.Model):

    _inherit = "res.partner"

    website_access_rights = fields.Selection(
        [('own', 'Own'),
        ('delegation', 'Delegation'),
        ('all', 'All')],
        string='Website access rights',
        default='own',
        required=True
    )

    show_history = fields.Boolean(
        string='Show history',
        default=True
    )

    show_invoices = fields.Boolean(
        string='Show invoices',
        default=True
    )

    show_all_catalogue = fields.Boolean(
        string='Show all products',
        help='If False the user will only see the products on his pricelist',
        default=True
    )

    show_customer_price = fields.Boolean(
        string='Show products with customer price in catalogue',
        help='If False the user will not see the products with customer price on the catalogue',
        default=True
    )

    order_validator = fields.Many2one('res.users', string='Orders Validator')
    global_order_validator = fields.Many2one('res.users', related='commercial_partner_id.order_validator', string='Global Orders Validator')
    active_portal_user = fields.Boolean('Usuario web activo', compute_sudo=True, compute="_compute_active_portal_user", search="_search_active_portal_user")
    external_review = fields.Boolean('Need external review (UVigo)')
    wholesaler = fields.Boolean('Mayorista')
    portfolio = fields.Boolean('Cliente cartera', default=True)

    def _search_active_portal_user(self, operator, operand):
        group_portal = self.env.ref('base.group_portal')
        users = self.env['res.groups'].sudo().search([('id', '=', group_portal.id)]).users
        #users = self.env['res.users'].sudo().search([(group_portal.id'groups_ids', 'in', )])
        partners = users.mapped('partner_id').ids
        partner_operator = ""
        if (
            operator == "="
            and operand == True
            or operator == "!="
            and operand == False
        ):
            partner_operator = "in"
        else:
            partner_operator = "not in"
        return [("id", partner_operator, partners)]
        

    def _compute_active_portal_user(self):
        group_portal = self.env.ref('base.group_portal')
        for partner in self:
            if partner.user_ids and group_portal  in partner.user_ids.groups_id:
                partner.active_portal_user =  True 
            else: 
                partner.active_portal_user = False
            

    def _get_domain_partner(self):
        if self.website_access_rights == 'own':
            return self.env['res.partner'].browse(self.id)
        elif self.website_access_rights == 'delegation':
            return self.env['res.partner'].browse(self.parent_id.id or self.id)
        elif self.website_access_rights == 'all':
            return self.env['res.partner'].browse(self.commercial_partner_id.id or self.id)

    @api.multi
    def write(self, vals):
        res = super(ResPartnerAccess, self).write(vals)
        for user in self:
            user_ids = self.env['res.users'].search([('partner_id', '=', user.id)])
            if 'website_access_rights' in vals:
                for user_id in user_ids:
                    group_sale_access_parent_id = self.env.ref('website_base.group_sale_access_parent_id')
                    group_sale_access_commercial_partner_id = self.env.ref('website_base.group_sale_access_commercial_partner_id')
                    if vals['website_access_rights'] == 'delegation':
                        if group_sale_access_parent_id.id not in user_id.groups_id.ids:
                            user_id.update({'groups_id': [(4, group_sale_access_parent_id.id)]})
                        if group_sale_access_commercial_partner_id.id in user_id.groups_id.ids:
                            user_id.update({'groups_id': [(3, group_sale_access_commercial_partner_id.id)]})
                    elif vals['website_access_rights'] == 'all':
                        if group_sale_access_commercial_partner_id.id not in user_id.groups_id.ids:
                            user_id.update({'groups_id': [(4, group_sale_access_commercial_partner_id.id)]})
                    else:
                        if group_sale_access_commercial_partner_id.id in user_id.groups_id.ids:
                            user_id.update({'groups_id': [(3, group_sale_access_commercial_partner_id.id)]})
                        if group_sale_access_parent_id.id in user_id.groups_id.ids:
                            user_id.update({'groups_id': [(3, group_sale_access_parent_id.id)]})
        return res

    @api.onchange('order_validator')
    def _onchange_order_validator(self):
        
        sale_model = self.env['ir.model'].search([('model', '=', 'sale.order')])
        partner_id = self.env['res.partner'].browse(self._origin.id)
        definition_domain = '["&", ["team_id.team_type", "=", "website"], ["partner_id", "child_of", {}]]'.format(partner_id.id)
        prev_definitions = self.env['tier.definition'].search([('definition_domain', '=', definition_domain)])
        if self.order_validator:
            print(self.order_validator)
            values = {
                'name': _("Validator for partner: {}".format(self.name)),
                'model_id': sale_model.id,
                'model': 'sale.order',
                'review_type': 'individual',
                'definition_type': 'domain',
                'active': True,
                'sequence': 30,
                'company_id': self.env.user.partner_id.company_id.id,
                'reviewer_id': self.order_validator.id,
                'notify_on_create': True,
                'definition_domain': definition_domain
            }

            if prev_definitions:
                for definition in prev_definitions:
                    definition.write(values)
            else:
                tier_definition = self.env['tier.definition'].create(values)
        else:
            print ("sin validador")
            if prev_definitions:
                print ("sin validador, con definicion encontrada")
                for definition in prev_definitions:
                    definition.unlink()