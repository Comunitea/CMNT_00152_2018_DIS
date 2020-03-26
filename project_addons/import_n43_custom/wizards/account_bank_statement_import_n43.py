# Copyright 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'

    
    def _get_partner_from_santander(self, conceptos):
        partner_obj = self.env['res.partner']
        partner = partner_obj.browse()
        # Try to match from VAT included in concept complementary record #01
        if conceptos.get('01'):
            if conceptos['01'][1]:
                vat = conceptos['01'][1]
                if vat:
                    partner = partner_obj.search(
                        [('vat', 'ilike', vat)], limit=1)
        if not partner:
            # Try to match from partner name
            if conceptos.get('01'):
                name = conceptos['01'][0][17:37]
                if name:
                    partner = partner_obj.search(
                        [('name', 'ilike', name)], limit=1)
        if not partner:
        # Try to match from partner name
            if conceptos.get('01'):
                name = conceptos['01'][0][7:27]
                if name:
                    partner = partner_obj.search(
                        [('name', 'ilike', name)], limit=1)
        return partner
