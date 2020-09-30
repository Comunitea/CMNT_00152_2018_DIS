# © 2018 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api


class Pricelist(models.Model):

    _inherit = "product.pricelist"

    is_promotion = fields.Boolean("Promotion", default=False)
    date_start = fields.Date(
        "Start Date", help="Starting date for the pricelist item validation"
    )
    date_end = fields.Date(
        "End Date", help="Ending valid for the pricelist item validation"
    )
    error_ids = fields.One2many(
        "product.pricelist.import.error", "import_id", "Error items"
    )

    @api.multi
    def search_promotion(self, product_id, qty, date):
        if not date:
            date = self._context.get("date") or fields.Date.context_today(self)
        if not qty:
            qty = 1
        domain = [
            ("product_id", "=", product_id),
            ("pricelist_id.is_promotion", "=", True),
            ("date_start", "<=", date),
            ("date_end", ">=", date)
            
        ]
        rules = self.env["product.pricelist.item"].search(
            domain, order="min_quantity asc"
        )
        correct_rule = False
        for rule in rules:
            if rule.min_quantity and qty < rule.min_quantity:
                continue
            else:
                correct_rule = rule
        return correct_rule

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if not any(arg[0] == "is_promotion" for arg in args):
            args += [("is_promotion", "!=", True)]
        return super(Pricelist, self).search(
            args, offset=offset, limit=limit, order=order, count=count
        )

    @api.multi
    def show_items_list(self, context=None):
        domain = [("pricelist_id", "=", self.id)]

        return {
            "type": "ir.actions.act_window",
            "res_model": "product.pricelist.item",
            "view_type": "form",
            "view_mode": "tree,form",
            'view_id ref="product.product_pricelist_item_tree_view"': "",
            "target": "current",
            "domain": domain,
        }

    @api.multi
    def show_error_list(self, context=None):
        domain = [("import_id", "=", self.id)]

        return {
            "type": "ir.actions.act_window",
            "res_model": "product.pricelist.import.error",
            "view_type": "form",
            "view_mode": "tree,form",
            'view_id ref="view_product_pricelist_import_error_tree"': "",
            "target": "current",
            "domain": domain,
        }
