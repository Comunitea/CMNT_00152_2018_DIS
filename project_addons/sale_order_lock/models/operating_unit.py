# Copyright 2015-2017 Eficent
# - Jordi Ballester Alomar
# Copyright 2015-2017 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class OperatingUnit(models.Model):

    _inherit = 'operating.unit'
    _description = 'Operating Unit'

    min_margin = fields.Float('Min Margin', help="If Margin of sale order \
        is below the min_margin the order will be locked")
