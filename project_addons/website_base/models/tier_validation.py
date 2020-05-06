# Copyright 2020 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval

class TierValidation(models.AbstractModel):
    _inherit = "tier.validation"

    @api.model
    def _calc_reviews_validated(self, reviews):
        """Override for different validation policy."""
        if not reviews:
            return False
        return not any([s != 'approved' for s in reviews.mapped('status')])