# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartnerAccess(models.Model):

    _inherit = "res.partner"

    portfolio = fields.Boolean('Cliente cartera', default=True)

