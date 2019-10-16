# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models
from datetime import datetime, timedelta


class ResPartner(models.Model):

    _inherit = "res.partner"

    sales_in_last_six_months = fields.Boolean(
        compute="_compute_sales_in_last_six_months",
        search="_search_sales_in_last_six_months",
    )

    def _search_sales_in_last_six_months(self, operator, operand):
        six_months_ago = datetime.now() + timedelta(days=-180)
        six_months_ago = six_months_ago.strftime("%Y-%m-%d")
        sale_order_groups = self.env["sale.order"].read_group(
            domain=[("date_order", ">=", six_months_ago)],
            fields=["partner_id"],
            groupby=["partner_id"],
        )
        partners = [x["partner_id"][0] for x in sale_order_groups]
        partner_operator = ""
        if (
            operator == "="
            and operand == True
            or operator == "!="
            and operand == False
        ):
            partner_operator = "in"
        else:
            partner_operator = "not in"
        return [("id", partner_operator, partners)]

    def _compute_sales_in_last_six_months(self):
        all_partners = self.search([("id", "child_of", self.ids)])
        all_partners.read(["parent_id"])
        six_months_ago = datetime.now() + timedelta(days=-180)
        six_months_ago = six_months_ago.strftime("%Y-%m-%d")
        sale_order_groups = self.env["sale.order"].read_group(
            domain=[
                ("partner_id", "in", all_partners.ids),
                ("date_order", ">=", six_months_ago),
            ],
            fields=["partner_id"],
            groupby=["partner_id"],
        )
        for group in sale_order_groups:
            partner = self.browse(group["partner_id"][0])
            while partner:
                if partner in self:
                    partner.sales_in_last_six_months = True
                partner = partner.parent_id
