# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.osv import expression


class StockMove(models.Model):
    _inherit = "stock.move"

    exclude_compute_cost = fields.Boolean(
        "Not include in costs",
        default=False,
        help="If true, this move is from a purchase, no include in cost computes",
    )

    @api.model
    def _get_all_base_domain(self, company_id=False):
        domain = super()._get_all_base_domain(company_id=company_id)
        if "exclude_compute_cost" in self._context:
            domain = expression.AND(
                [
                    [
                        (
                            "exclude_compute_cost",
                            "=",
                            not self._context.get("exclude_compute_cost"),
                        )
                    ],
                    expression.normalize_domain(domain),
                ]
            )

        return domain

    @api.model
    def _get_in_base_domain(self, company_id=False):
        domain = super()._get_in_base_domain(company_id=company_id)
        if "exclude_compute_cost" in self._context:
            domain = expression.AND(
                [
                    [
                        (
                            "exclude_compute_cost",
                            "=",
                            not self._context.get("exclude_compute_cost"),
                        )
                    ],
                    expression.normalize_domain(domain),
                ]
            )

        return domain
