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

    def _get_domain_partner(self):
        if self.website_access_rights == 'own':
            return self.env['res.partner'].browse(self.id)
        elif self.website_access_rights == 'delegation':
            return self.env['res.partner'].browse(self.parent_id.id)
        elif self.website_access_rights == 'all':
            return self.env['res.partner'].browse(self.commercial_partner_id.id)