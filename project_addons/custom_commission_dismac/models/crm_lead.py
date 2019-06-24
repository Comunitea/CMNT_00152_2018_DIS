# -*- coding: utf-8 -*-

from odoo import api, models, fields


class CrmLead(models.Model):
    _inherit = "crm.lead"

    pointing = fields.Boolean('Is pointing')
    pointing_per = fields.Float('Poiting (%)')
