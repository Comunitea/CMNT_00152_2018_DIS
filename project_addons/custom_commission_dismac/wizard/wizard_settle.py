# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields


class SaleCommissionMakeSettle(models.TransientModel):
    _inherit = "sale.commission.make.settle"

    by_goals = fields.Boolean('By Goals', default=True)

    @api.multi
    def action_settle(self):
        """
        Compute settlements by goals
        """
        res = super().action_settle()
        sett_ids = []
        sett_objs = self.env['sale.commission.settlement']

        if res.get('domain', False):
            sett_ids = res['domain'][0][2]
            sett_objs = self.env['sale.commission.settlement'].browse(sett_ids)

        if sett_objs and self.by_goals:
            sett_objs.write({'by_goals': self.by_goals})

            for sett in sett_objs:
                sett.settlement_by_goal()
        return res
