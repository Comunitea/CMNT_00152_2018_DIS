# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval


class TierValidation(models.AbstractModel):
    _inherit = "tier.validation"

    @api.multi
    def request_validation(self):
        created_trs = super().request_validation()
        td_obj = self.env["tier.definition"]
        for rec in self:
            if getattr(rec, self._state_field) in self._state_from:
                if rec.need_validation:
                    tier_definitions = td_obj.search(
                        [("model", "=", self._name)], order="sequence desc"
                    )
                    for td in tier_definitions:
                        if self.evaluate_tier(td):
                            # Create Activity for Reviewer
                            try:
                                activity_type_id = self.env.ref(
                                    "sale_tier_validation_dismac.mail_activity_data_validation"
                                ).id
                            except ValueError:
                                activity_type_id = False
                            ctx = self._context.copy()
                            ctx.update(skip_check_locks=True)
                            self.act1 = (
                                self.env["mail.activity"]
                                .with_context(ctx)
                                .create(
                                    {
                                        "activity_type_id": activity_type_id,
                                        "note": "Request Validation",
                                        "res_id": rec.id,
                                        "res_model_id": td.model_id.id,
                                        "user_id": td.reviewer_id.id,
                                    }
                                )
                            )
                    # TODO: notify? post some msg in chatter?
        return created_trs
