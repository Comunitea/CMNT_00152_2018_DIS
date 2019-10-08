# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class PartnerZone(models.Model):

    _name = 'partner.zone'

    name = fields.Char('Name', required=True)
