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

    def _get_domain_partner(self):
        if self.website_access_rights == 'own':
            return self.env['res.partner'].browse(self.id)
        elif self.website_access_rights == 'delegation':
            return self.env['res.partner'].browse(self.parent_id.id or self.id)
        elif self.website_access_rights == 'all':
            return self.env['res.partner'].browse(self.commercial_partner_id.id or self.id)


    @api.onchange('order_validator')
    def _onchange_order_validator(self):
        if self.order_validator:
            sale_model = self.env['ir.model'].search([('model', '=', 'sale.order')])
            partner_id = self.env['res.partner'].browse(self._origin.id)

            if partner_id:
                definition_domain = '["&", ["team_id.team_type", "=", "website"], ["partner_id", "child_of", {}]]'.format(partner_id.id)
                values = {
                    'name': _("Validator for partner: {}".format(partner_id.name)),
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

                prev_definitions = self.env['tier.definition'].search([('definition_domain', '=', definition_domain)])
                for definition in prev_definitions:
                    definition.write({
                        'active': False
                    })
                tier_definition = self.env['tier.definition'].create(values)