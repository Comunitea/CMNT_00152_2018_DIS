# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.osv import expression

class StockMove(models.Model):
    _inherit = 'stock.move'

    exclude_compute_cost = fields.Boolean('Not include in costs', default=False,
                                          help="If true, this move is from a purchase, no include in cost computes")

    @api.model
    def _get_all_base_domain(self, company_id=False):
        domain = super()._get_all_base_domain(company_id = company_id)
        if 'exclude_compute_cost' in self._context:
            domain = expression.AND([[('exclude_compute_cost','=', not self._context.get('exclude_compute_cost'))], domain])
        return domain

    @api.model
    def _get_in_base_domain(self, company_id=False):
        domain = super()._get_in_base_domain(company_id=company_id)
        if 'exclude_compute_cost' in self._context:
            domain = expression.AND(
                [[('exclude_compute_cost', '=', not self._context.get('exclude_compute_cost'))], domain])
        return domain

    @api.model
    def run_fifo_pricelist_cost(self, move, quantity=None):
        valued_move_lines = move.move_line_ids.filtered(lambda ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
        valued_quantity = 0
        new_price_list_cost = 0
        for valued_move_line in valued_move_lines:
            valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
        qty_to_take_on_candidates = quantity or valued_quantity
        candidates = move.product_id._get_fifo_candidates_in_move()
        for candidate in candidates:
            new_price_list_cost = candidate.price_unit
            if candidate.remaining_qty <= qty_to_take_on_candidates:
                qty_taken_on_candidate = candidate.remaining_qty
            else:
                qty_taken_on_candidate = qty_to_take_on_candidates
            qty_to_take_on_candidates -= qty_taken_on_candidate

            if qty_to_take_on_candidates == 0:
                break

        if new_price_list_cost:
            product = move.product_id.sudo()
            product.pricelist_cost = new_price_list_cost
            product._compute_reference_cost()
            #product.reference_cost = new_price_list_cost * product.product_tmpl_id.cost_ratio_id.purchase_ratio


    @api.model
    def _run_fifo(self, move, quantity=None):
        ## no puedo heredar y llamar 2 veces ya que marca los movimientos, por lo que la segunda llamada estaŕia mal
        ## replico en en run_fifo_pricelist_cost sin escribir nada
        if move.product_id.cost_method == 'fifo':
            ctx = move._context.copy()
            ctx.update(exclude_compute_cost=True)
            move_pricelist_cost = move.with_context(ctx)
            self.run_fifo_pricelist_cost(move=move_pricelist_cost, quantity=quantity)
        return super()._run_fifo(move=move, quantity=quantity)
