# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, registry, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools import float_is_zero
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
            move.write({'move_dest_ids': [(6, 0, [new_move.id])]})
            new_move._action_confirm()
            move.write({'move_dest_ids': [(6, 0, [new_move.id])]})
        else:
            return super()._run_push(move=move)

class StockMove(models.Model):

    _inherit = 'stock.move'

    to_split_process = fields.Boolean('Para dividir', copy=False, default=False)
    new_picking_id = fields.Many2one('stock.picking', string="Asignar a un nuevo picking")
    show_advance = fields.Boolean('Mostrar/ocultar avanzado', store=False)
    sale_id = fields.Many2one(related='sale_line_id.order_id', string="Venta" )
    picking_id_sale_id= fields.Many2one(related='picking_id.sale_id', string="Venta")

    @api.multi
    def picking_change(self):
        for move in self:
            if move.new_picking_id:
                body = "El usuario {} ha sacado el movimiento {} y se ha movido al albarán  {}".format(self.env.user.display_name, move.name, move.new_picking_id.name)
                move.picking_id.message_post(body=body)
                body = "El usuario {} ha traido el movimiento {} y del albarán {}".format(
                    self.env.user.display_name, self.name, self.picking_id.name)
                move.new_picking_id.message_post(body=body)
                sql = "update stock_move set picking_id={} where id={}".format(move.new_picking_id.id, move.id)
                self._cr.execute(sql)
                self._cr.commit()

    @api.multi
    def back_to_confirm(self):
        for move in self:
            move.action_back_to_draft()
            move._action_confirm()

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        if self._context.get('write_message', False):
            body = "El usuario {} ha cancelado el movimiento {}".format(self.env.user.display_name, self.name)
            self.picking_id.message_post(body=body)
            self._action_cancel()

            action = self.env.ref('stock.stock_picking_action_picking_type').read()[0]
            view_form = self.env.ref(
                'stock.'
                'view_picking_form')

            action['context'] = {'search_default_picking_type_id': [self.picking_type_id.id],
             'default_picking_type_id': self.picking_type_id.id,
             'contact_display': 'partner_address', }

            action['res_id'] = self.id
            action['views'] = [(view_form.id, 'form')]
            action['view_id'] = view_form.id
            action['view_mode'] = 'form'
            return action

    def _action_done(self):
        return super(StockMove, self)._action_done()
        # for move in self:
        #     for ml in move.move_line_ids:
        #         ml._push_apply(move)
        #auto_picks = self.mapped('move_dest_ids').filtered(lambda x: x.rule_id.model == 'move.line' and x.rule_id.auto == 'manual').mapped('picking_id')
        import pdb; pdb.set_trace()
        res = super(StockMove, self)._action_done()
        #if auto_picks:
        #    auto_picks.action_done()
        return res
        ##TODO MEJORAR ESTO PARA NO LLAMAR SIEMPRE
        for move in self:
            for ml in move.move_line_ids:
                ml._push_apply(move)
        return res

    def _action_assign(self):
        res = super()._action_assign()
        # moves = self.filtered(lambda x: x.picking_type_id.auto_fill_operation)
        # if moves:
        #     moves.force_set_qty_done(reset=False)
        return res


    def _recompute_state(self):
        # if self._context.get('update_qty_done'):
        #     self._action_assign()
        return super()._recompute_state()

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _free_reservation(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, ml_to_ignore=None):
        """ Esto es una copia del inicio del _free_reservation para poder lanzar un raise si procede
            - Lanzo un raise si hay cantidad reservada y viene de un ajsute de inventario
            - Además pongo la qty_done = product_uom_qty si procede """

        self.ensure_one()

        if ml_to_ignore is None:
            ml_to_ignore = self.env['stock.move.line']
        ml_to_ignore |= self

        # Check the available quantity, with the `strict` kw set to `True`. If the available
        # quantity is greather than the quantity now unavailable, there is nothing to do.
        available_quantity = self.env['stock.quant']._get_available_quantity(
            product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True
        )
        if quantity > available_quantity:
            # We now have to find the move lines that reserved our now unavailable quantity. We
            # take care to exclude ourselves and the move lines were work had already been done.
            outdated_move_lines_domain = [
                ('state', 'in', ['assigned', 'partially_available']),
                ('qty_done', '>', 0),
                ('product_id', '=', product_id.id),
                ('lot_id', '=', lot_id.id if lot_id else False),
                ('location_id', '=', location_id.id),
                ('owner_id', '=', owner_id.id if owner_id else False),
                ('package_id', '=', package_id.id if package_id else False),
                ('product_qty', '>', 0.0),
                ('id', 'not in', ml_to_ignore.ids),
            ]
            outdated_candidates = self.env['stock.move.line'].search_count(outdated_move_lines_domain)
            if outdated_candidates > 0 and self._context.get('from_stock_inventory', False):
                raise ValidationError (_('No pedes realizar un ajuste para el artículo:\n {}\n ya que tienes movimientos asociados que se quedarían sin reserva'.format(product_id.display_name)))

        ctx = self._context.copy()
        ctx.update(update_qty_done=True)
        res = super(StockMoveLine, self.with_context(ctx))._free_reservation(product_id=product_id, location_id=location_id, quantity=quantity, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                          ml_to_ignore=ml_to_ignore)

        if outdated_candidates > 0:
            rounding = self.product_uom_id.rounding
            outdated_candidates = self.env['stock.move.line'].search(outdated_move_lines_domain)
            outdated_candidates.filtered(lambda x: float_is_zero(x.product_uom_qty, precision_rounding=rounding)).unlink()
            outdated_candidates.filtered(lambda x: not float_is_zero(x.qty_done, precision_rounding=rounding)).with_context(ctx).force_assigned_qty_done(reset=False)
        return res

    def _push_apply(self, move):
        ##Esto es una copia de _push_apply pero para move line
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
