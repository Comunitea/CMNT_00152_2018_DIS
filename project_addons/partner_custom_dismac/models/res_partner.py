# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

class ResPartner(models.Model):
    _inherit = 'res.partner'

    claimable_on = fields.Datetime('Partner will be claimable on this date', compute="_get_partner_claim_date")
    is_claimable = fields.Boolean('Is the partner claimable?', compute="_get_partner_claim_status")
    claimed_on = fields.Datetime('Claimed on', default=lambda self: fields.datetime.now())

    @api.multi
    def _get_partner_claim_date(self):
        sale_order_obj = self.env['sale.order'].search([('partner_id', '=', self.id)], limit=1, order='id desc')

        if not sale_order_obj:
            sale_order_type_obj = self.env['sale.order.type'].search([], limit=1)
            claimable_on = datetime.strptime(self.create_date, '%Y-%m-%d %H:%M:%S')+relativedelta(days =+ sale_order_type_obj.days_without_order_or_quotation)
            unclaimed_for = datetime.strptime(self.claimed_on, '%Y-%m-%d %H:%M:%S')+relativedelta(days =+ sale_order_type_obj.unclaimable_for)
        else:
            claimable_on = datetime.strptime(sale_order_obj.date_order, '%Y-%m-%d %H:%M:%S')+relativedelta(days =+ sale_order_obj.type_id.days_without_order_or_quotation)
            unclaimed_for = datetime.strptime(self.claimed_on, '%Y-%m-%d %H:%M:%S')+relativedelta(days =+ sale_order_obj.type_id.unclaimable_for)

        if not claimable_on or not unclaimed_for:
            if claimable_on:
                self.claimable_on = claimable_on
            if unclaimed_for:
                self.claimable_on = unclaimed_for
        else:
            self.claimable_on = self._compare_dates(claimable_on, unclaimed_for)
        
    @api.multi
    def _get_partner_claim_status(self):
        if self.claimable_on:
            today_date = datetime.now()
            claimable_on = datetime.strptime(self.claimable_on, '%Y-%m-%d %H:%M:%S')
            if (claimable_on <= today_date):
                self.is_claimable = True
            else:
                self.is_claimable = False

    @api.multi
    def _compare_dates(self, date1, date2):
        if(date1>date2):
            return date1
        if(date2>date1):
            return date2
        if(date1==date2):
            return date1

    @api.multi
    @api.onchange('user_id')
    def _update_claimed_on_date(self):
        for partner in self:
            partner.claimed_on = datetime.now()