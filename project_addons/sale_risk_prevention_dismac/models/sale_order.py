# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class RiskPreventionDocumentSale(models.Model):
    _name = "risk.prevention.document.sale"

    document = fields.Char("Document", required=True)
    file = fields.Binary(string="File", required=True, attachment=True)
    sale_order_id = fields.Many2one("sale.order")


class SaleOrder(models.Model):

    _inherit = "sale.order"

    opt_prevention_risk = fields.Boolean(
        related="type_id.opt_prevention_risk", readonly=True
    )
    need_prevention_risk = fields.Selection([('1', 'Sí '),
                                             ('0', 'No')],
                                            string="Need Prevention Risk")
    request_prevention = fields.Boolean(string="Request prevention risk")
    prevention_risk_contact_id = fields.Many2one(
        "res.partner",
        string="Prevention Contact",
        domain="[('company_type', '=', 'person')]",
    )
    installation_explanation = fields.Text("Installation Explanation")
    subcontracts = fields.Text("Subcontracts")
    risk_document_ids = fields.One2many(
        string="Prevention Documents",
        comodel_name="risk.prevention.document.sale",
        inverse_name="sale_order_id",
    )
    risk_document_completed = fields.Boolean(
        string="Risk document " "completed", default=False
    )

    @api.multi
    def action_confirm(self):
        """
        Check if order requires prevention
        """
        for order in self:
            if (
                order.opt_prevention_risk
                and order.need_prevention_risk == False
            ):
                msg = _(
                    "Es necesario definir si es necesaria la preveciónde riesgos antes de confirmar el pedido"
                )
                raise UserError(msg)
        res = super().action_confirm()
        return res