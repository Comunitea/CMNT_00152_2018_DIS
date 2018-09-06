# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class ResPartner(models.Model):

    _inherit = 'res.partner'

    @api.multi
    def _compute_valid_mandate_id(self):
        """
            Priorizamos los mandatos del propio partner
            sobre los del commercial_partner_id.
            Los partners que no tengan mandato se mandan a super.
        """
        company_id = self.env.context.get('force_company', False)
        if company_id:
            company = self.env['res.company'].browse(company_id)
        else:
            company = self.env['res.company']._company_default_get(
                'account.banking.mandate')
        super_partners = self.env['res.partner']
        for partner in self:
            mandates = partner.bank_ids.mapped(
                'mandate_ids').filtered(
                lambda x: x.state == 'valid' and x.company_id == company)
            first_valid_mandate_id = mandates[:1].id
            if not first_valid_mandate_id:
                super_partners += partner
            else:
                partner.valid_mandate_id = first_valid_mandate_id
        if super_partners:
            return super(ResPartner,
                         super_partners)._compute_valid_mandate_id()
