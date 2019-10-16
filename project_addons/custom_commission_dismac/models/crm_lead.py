# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class CrmLead(models.Model):
    _inherit = "crm.lead"

    pointing = fields.Boolean("Is pointing")
    pointing_per = fields.Float("Poiting (%)")
