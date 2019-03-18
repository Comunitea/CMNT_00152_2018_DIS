# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pprint import pprint

class ResPartner(models.Model):
    _inherit = 'res.partner'

    claimable_on = fields.Datetime('Partner will be claimable on this date', compute="_get_partner_claim_date")
    is_claimable = fields.Boolean('Is the partner claimable?', compute="_get_partner_claim_date")
    claimed_on = fields.Datetime('Claimed on', default=lambda self: fields.datetime.now())

    unclaimable_for = fields.Integer(related="sale_type.unclaimable_for")
    days_without_order_or_quotation = fields.Integer(related="sale_type.days_without_order_or_quotation")

    @api.multi
    def _get_partner_claim_date(self):

        for partner in self:
            sale_order_obj = self.env['sale.order'].search([('partner_id', '=', partner.id)], limit=1, order='id desc')    
            claimable_on = datetime.strptime(sale_order_obj and sale_order_obj.date_order or partner.create_date, '%Y-%m-%d %H:%M:%S')+relativedelta(days =+ partner.days_without_order_or_quotation or sale_order_obj.type_id.days_without_order_or_quotation)
            unclaimed_for = datetime.strptime(partner.claimed_on, '%Y-%m-%d %H:%M:%S')+relativedelta(days =+ partner.unclaimable_for or sale_order_obj.type_id.unclaimable_for)
            end_claimable_on = max(claimable_on, unclaimed_for)

            today_date = datetime.now()
            if (end_claimable_on <= today_date):
                is_claimable = True
            else:
                is_claimable = False
            partner.claimable_on = end_claimable_on
            partner.is_claimable = is_claimable

    @api.multi
    @api.onchange('user_id')
    def _onchange_user_id(self):
        for partner in self:
            partner.claimed_on = datetime.now()