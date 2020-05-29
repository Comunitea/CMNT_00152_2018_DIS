# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields


class ChangeAgentInvoiceWzd(models.TransientModel):
    _name = "change.agents.invoice.wzd"

    @api.model
    def _default_line_ids(self):
        lines = []
        active_ids = self._context.get("active_ids", [])
        visited_agents_ids = []
        for invoice in self.env["account.invoice"].browse(active_ids):
            for agent_line in invoice.mapped("invoice_line_ids.agents"):
                if agent_line.agent.id in visited_agents_ids:
                    continue

                vals = {
                    "agent": agent_line.agent.id,
                    "commission": agent_line.commission.id,
                    "reduction_per": agent_line.reduction_per,
                }
                lines.append((0, 0, vals))
                visited_agents_ids.append(agent_line.agent.id)
        return lines

    line_ids = fields.One2many(
        comodel_name="change.agents.lines.invoice.wzd",
        inverse_name="wzd_id",
        string="Change Agents lines",
        default=_default_line_ids,
    )

    @api.multi
    def set_agents_lines(self):
        active_ids = self._context.get("active_ids", [])
        new_agents = []
        for line in self.line_ids:
            vals = {
                "agent": line.agent.id,
                "commission": line.commission.id,
                "reduction_per": line.reduction_per,
            }
            new_agents.append((0, 0, vals))

        invoices = self.env["account.invoice"].browse(active_ids)
        invoices.mapped("invoice_line_ids.agents").unlink()
        invoices.mapped("invoice_line_ids").write({"agents": new_agents})
        return


class ChangeAgentsLinesInvoiceWzd(models.TransientModel):
    _name = "change.agents.lines.invoice.wzd"

    wzd_id = fields.Many2one("change.agents.invoice.wzd", "Wizard")

    agent = fields.Many2one(
        comodel_name="res.partner",
        domain="[('agent', '=', True)]",
        ondelete="restrict",
        required=True,
    )
    commission = fields.Many2one(
        comodel_name="sale.commission", ondelete="restrict", required=True
    )
    reduction_per = fields.Float(
        "% Over subtotal",
        default=100.0,
        help="Compute settlement with % reduced over invoices subtotal",
    )
