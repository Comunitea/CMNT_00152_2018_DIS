#© 2018Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class RiskPreventionDocument(models.Model):
    _name = 'risk.prevention.document'

    document = fields.Char('Document', required=True)
    file = fields.Binary(string="File", required=True)
    due_bool = fields.Boolean("Due", default=False)
    due_date = fields.Date(string='Due Date')
    partner_id = fields.Many2one('res.partner')
    partner_e_id = fields.Many2one('res.partner')


class ResPartner(models.Model):
    _inherit = 'res.partner'
    risk_document = fields.Boolean(string='Risk Document needed')
    risk_document_company_ids = fields.One2many(
        string='Prevention Company Documents',
        comodel_name='risk.prevention.document',
        inverse_name='partner_id',
    )
    risk_document_employee_ids = fields.One2many(
        string='Prevention Employee Documents',
        comodel_name='risk.prevention.document',
        inverse_name='partner_e_id',
    )
