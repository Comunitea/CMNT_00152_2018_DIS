# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from datetime import datetime


class Settlement(models.Model):
    _inherit = 'sale.commission.settlement'

    by_goals = fields.Boolean('By Goals')
    unit_line_ids = fields.One2many(
        'operating.unit.settlement.line', 'settlement',
        'Settlement by Operating Unit', readonly=True)
    settlemet_total = fields.Float(
        string='Settlement Total',
        compute="_compute_total",
        readonly=True,
        store=False)
    commission_total = fields.Float(
        string='Commission Total',
        compute="_compute_total",
        readonly=True,
        store=False)

    @api.multi
    def _compute_total(self):
        for sett in self:
            sett.settlemet_total = sum(x.amount for x in sett.unit_line_ids)
            sett.commission_total = \
                sum(x.commission for x in sett.unit_line_ids)

    @api.multi
    def delete_settlement_by_goal(self):
        self.ensure_one()
        self.unit_line_ids.unlink()

    @api.multi
    def settlement_by_goal(self):
        self.ensure_one()
        month_goal_obj = self.env['agent.month.goal']
        invoces_by_unit = {}

        # Agrupo Facturas porunidad operacional, (papelería, mobiliario...)
        for inv in self.lines.mapped('invoice'):
            # Líneas sin tipo de venta no comisionan
            if not inv.operating_unit_id:
                continue

            # Obtengo importe total y coeficiente sobre margen
            if inv.operating_unit_id not in invoces_by_unit:
                invoces_by_unit[inv.operating_unit_id] = {
                    'amount': 0.0, 'coef': 0.0, 'num': 0.0}
            invoces_by_unit[inv.operating_unit_id]['amount'] += \
                inv.amount_total
            invoces_by_unit[inv.operating_unit_id]['coef'] += inv.coef
            invoces_by_unit[inv.operating_unit_id]['num'] += 1

        month = datetime.strptime(self.date_to, '%Y-%m-%d').month

        for op_unit in invoces_by_unit:
            # Busco objetivos para el agente en el mes dado y para la unidad
            # operacional
            domain = [
                ('month', '=', month),
                ('agent_id', '=', self.agent.id),
                ('unit_id', '=', op_unit.id)
            ]
            month_goals = month_goal_obj.search(domain)
            if not month_goals:
                continue
            goal_types = month_goals.mapped('goal_type_id')
            amount_goal = month_goals.mapped('amount_goal')[0]
            if not goal_types:
                continue

            # Creo una línea por cada unidad operacional liquidada
            vals = {
                'settlement': self.id,
                'unit_id': op_unit.id
            }
            ousl = self.env['operating.unit.settlement.line'].create(vals)

            # Añado a unit_info el coeficiente de las facturas y el objetivo
            # para esa unidad operacional
            unit_info = invoces_by_unit[op_unit]
            unit_info.update({
                'amount_goal': amount_goal,
                'total_coef': unit_info['coef'] / unit_info['num']
            })

            # Creo una goal.line por cada objetivo dentro de la linea de unidad
            # operacional
            goal_line_vals = []
            for gt in goal_types:
                commission, note = gt.get_commission(unit_info)
                amount = unit_info['amount'] * (commission / 100.0)
                vals = {
                    'unit_line_id': ousl.id,
                    'goal_type_id': gt.id,
                    'note': note,
                    'commission': commission,
                    'amount': amount
                }
                goal_line_vals.append((0, 0, vals))

            ousl.write({'goal_line_ids': goal_line_vals})
        return

    def _prepare_invoice_line(self, settlement, invoice, product):
        """
        Si la liquidación es por objetivos, creo la liquidación de la factura
        con el precio por el nuevo campo de importe liquidado total
        """
        res = super()._prepare_invoice_line(settlement, invoice, product)
        if settlement.by_goals:
            res['price_unit'] = -settlement.settlemet_total \
                if invoice.type == 'in_refund' else settlement.settlemet_total
        return res

    # def _add_extra_invoice_lines(self, settlement):
    #     """
    #     Este hook podría estar bien si queremos respetar la creación de
    #     líneas de factura original mezclado con nuestro sistema de
    #     liquidación.
    #     """
    #     res = super()._add_extra_invoice_lines(settlement)
    #     return res


class OperatingUnitSettlementLine(models.Model):
    _name = 'operating.unit.settlement.line'

    settlement = fields.Many2one(
        "sale.commission.settlement", readonly=True, ondelete="cascade",
        required=True)
    unit_id = fields.Many2one(
        comodel_name='operating.unit', string='Operating Unit', required=True)
    commission = fields.Float('Commission Applied (%)',
                              compute='_compute_total')
    amount = fields.Float('Settlement Amount',
                          compute='_compute_total')
    goal_line_ids = fields.One2many(
        'goal.settlement.line', 'unit_line_id', 'Goal Lines', readonly=True)

    @api.depends('goal_line_ids', 'goal_line_ids.amount',
                 'goal_line_ids.commission')
    def _compute_total(self):
        for line in self:
            line.amount = sum(x.amount for x in line.goal_line_ids)
            line.commission = sum(x.commission for x in line.goal_line_ids)


class GoalSettlementLine(models.Model):
    _name = 'goal.settlement.line'

    unit_line_id = fields.Many2one(
        "operating.unit.settlement.line", readonly=True, ondelete="cascade",
        required=True)
    goal_type_id = fields.Many2one(
        comodel_name='goal.type', string='Type', required=False)
    note = fields.Text('Notes')
    commission = fields.Float('Commission Applied (%)')
    amount = fields.Float('Settlement Amount')
