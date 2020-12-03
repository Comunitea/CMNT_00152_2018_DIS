# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, fields
from datetime import timedelta

class CreditControlLine(models.Model):
    _inherit = "credit.control.line"

    @api.model
    def create_or_update_from_mv_lines(self, lines, level, controlling_date,
                                       check_tolerance=True, default_lines_vals=None):
        new_lines = super(CreditControlLine, self).create_or_update_from_mv_lines(lines, level, controlling_date, check_tolerance=check_tolerance, default_lines_vals=default_lines_vals)
        
        if level.level == 1:
            currency_obj = self.env['res.currency']
            user = self.env.user
            currencies = currency_obj.search([])

            tolerance = {}
            tolerance_base = user.company_id.credit_control_tolerance
            user_currency = user.company_id.currency_id
            for currency in currencies:
                tolerance[currency.id] = currency.compute(tolerance_base,
                                                        user_currency)
            
            unpaid_lines = self.env['credit.control.line'].search([
                ('policy_level_id', '=', level.id),
                ('state', '=', 'sent'),
                ('invoice_id.state', 'in', ['open'])
            ]).mapped('move_line_id')
            
            if unpaid_lines:
                for line in unpaid_lines:
                    ml_currency = line.currency_id
                    if ml_currency and ml_currency != user_currency:
                        open_amount = line.amount_residual_currency
                    else:
                        open_amount = line.amount_residual
                    cur_tolerance = tolerance.get(line.currency_id.id,
                                                tolerance_base)
                    if check_tolerance and open_amount < cur_tolerance:
                        continue
                    vals = self._prepare_from_move_line(line, level, controlling_date, open_amount, default_lines_vals)
                    line = self.create(vals)
                    new_lines |= line
        return new_lines

    def _recompute_state(self):
        for line in self.env['credit.control.line'].search([
                ('mail_message_id', '!=', False),
                ('write_date', '>=', fields.Datetime.to_string(fields.datetime.now() - timedelta(days=1)))
            ]):
            if line.mail_message_id.state == 'outgoing':
                line.update({'state': 'to_be_sent'})
            elif line.mail_message_id.state in ('sent', 'received'):
                line.update({'state': 'sent'})
            elif line.mail_message_id.state in ('exception', 'cancel'):
                line.update({'state': 'error'})
