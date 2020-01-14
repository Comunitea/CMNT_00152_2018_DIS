# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, registry, _
from odoo.osv import expression
from dateutil.relativedelta import relativedelta

class ProcurementGroup(models.Model):

    _inherit = 'procurement.group'

    @api.model
    def _search_rule(self, route_ids, product_id, warehouse_id, domain):
        if not ('model', '=', 'move.line') in domain:
            domain += [('model','=', 'move')]

        return super()._search_rule(route_ids=route_ids, product_id=product_id, warehouse_id=warehouse_id, domain=domain)

    @api.model
    def _search_rule_move_line(self, route_ids, product_id, warehouse_id, domain):
        """ First find a rule among the ones defined on the procurement
        group, then try on the routes defined for the product, finally fallback
        on the default behavior
        """
        domain += [('model', '=', 'move.line')]
        return super()._search_rule(route_ids=route_ids, product_id=product_id, warehouse_id=warehouse_id,
                                    domain=domain)


class StockRule(models.Model):

    _inherit = 'stock.rule'

    model = fields.Selection(selection=[('move', 'Movimiento'), ('move.line', 'Operación')], default='move')

    def _run_push(self, move):
        """ Apply a push rule on a move.
        If the rule is 'no step added' it will modify the destination location
        on the move.
        If the rule is 'manual operation' it will generate a new move in order
        to complete the section define by the rule.
        Care this function is not call by method run. It is called explicitely
        in stock_move.py inside the method _push_apply
        """
        if self.model == 'move.line' and self.auto == 'manual':
            location_id = self.location_src_id
            location_dest_id = self.location_id
            new_date = fields.Datetime.to_string(move.date_expected + relativedelta(days=self.delay))
            new_move_vals = self._push_prepare_move_copy_values(move, new_date)
            new_move_vals.update({'rule_id': self.id,
                                  'location_id': location_id.id,
                                  'location_dest_id': location_dest_id.id})
            new_move = move.sudo().copy(new_move_vals)
            new_move._action_confirm()
            move.write({'move_dest_ids': [(6, 0, [new_move.id])]})
        else:
            return super()._run_push(move=move)

class StockMove(models.Model):

    _inherit = 'stock.move'

    def _action_done(self):

        for move in self:
            for ml in move.move_line_ids:
                ml._push_apply(move)
        auto_picks = self.mapped('move_dest_ids').filtered(lambda x: x.rule_id.model == 'move.line' and x.rule_id.auto == 'manual').mapped('picking_id')
        res = super(StockMove, self)._action_done()
        if auto_picks:
            auto_picks.action_done()
        return res

class StockLine(models.Model):
    _inherit = 'stock.move.line'


    def _push_apply(self, move):
            # if the move is already chained, there is no need to check push rules
        if move.move_dest_ids:
            return False
        # if the move is a returned move, we don't want to check push rules, as returning a returned move is the only decent way
        # to receive goods without triggering the push rules again (which would duplicate chained operations)
        domain = [('model', '=', 'move.line'), ('location_src_id', '=', self.location_dest_id.id), ('action', 'in', ('push', 'pull_push'))]
        # first priority goes to the preferred routes defined on the move itself (e.g. coming from a SO line)
        warehouse_id = move.warehouse_id or move.picking_id.picking_type_id.warehouse_id
        if not self.env.context.get('force_company',
                                    False) and self.location_dest_id.company_id == self.env.user.company_id:
            rules = self.env['procurement.group']._search_rule(move.route_ids, move.product_id, warehouse_id,
                                                               domain)
        else:
            rules = self.sudo().env['procurement.group']._search_rule(move.route_ids, move.product_id, warehouse_id,
                                                                      domain)
        # Make sure it is not returning the return
        if rules and (
                not move.origin_returned_move_id or move.origin_returned_move_id.location_dest_id.id != rules.location_id.id):
            rules._run_push(move)
