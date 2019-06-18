# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
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
        invoices_by_unit = {}  # agrupo las facturas por unidad operacional
        # Conveniente ver el global de todas
        invoices_by_global = {
            'amount': 0.0, 'coef': 0.0, 'num': 0.0,
            'amount_goal': 0.0, 'total_coef': 0.0, 'reduced_amount': 0.0
        }

        # Agrupo Facturas por unidad operacional, (papelería, mobiliario...)
        for inv in self.lines.mapped('invoice'):
            # Líneas sin tipo de venta no comisionan
            # if not inv.operating_unit_id:
            #     continue
            # Obtengo importe total y coeficiente sobre margen
            if inv.operating_unit_id not in invoices_by_unit:
                invoices_by_unit[inv.operating_unit_id] = {
                    'amount': 0.0, 'coef': 0.0, 'num': 0.0, 
                    'reduced_amount': 0.0}
            invoices_by_unit[inv.operating_unit_id]['amount'] += \
                inv.amount_untaxed
            invoices_by_global['amount'] += inv.amount_untaxed
            invoices_by_unit[inv.operating_unit_id]['coef'] += inv.coef
            invoices_by_global['coef'] += inv.coef
            invoices_by_unit[inv.operating_unit_id]['num'] += 1
            invoices_by_global['num'] += 1

            # Si hay comisiones con señalamiento, obtenemos el % de
            # reduction_per definido en la línea de agent
            reduced_amount = inv.get_reduced_amount(self.agent)
            invoices_by_unit[inv.operating_unit_id]['reduced_amount'] += \
                reduced_amount
            invoices_by_global['reduced_amount'] += reduced_amount

        month = datetime.strptime(self.date_to, '%Y-%m-%d').month

        global_goal_types = self.env['goal.type']
        min_goal_types = self.env['goal.type']  # special case

        # Calculo las líneas por unidad operacional
        # excluyendo aqueyas líneas que solo tengan un objetivo de tipo
        # venta y con unidades globales establecido
        # Compruebo en el siguiente bucle si tengo que crear líneas para
        # objetivos de este tipo
        for op_unit in invoices_by_unit:
            # Busco objetivos para el agente en el mes dado y para la unidad
            # operacional
            domain = [
                ('month', '=', month),
                ('agent_id', '=', self.agent.id),
                # ('|') TODO
                ('unit_id', '=', op_unit.id)
                # ('unit_id', '=', False)
            ]
            month_goals = month_goal_obj.search(domain)
            if not month_goals:
                continue
            goal_types = month_goals.mapped('goal_type_id')
            if not goal_types:
                continue

            # Si solo hay un objetivo y este es de ventas calculo por unidades
            # global lo dejamos para luego, y ya no creo línea por unidad
            if len(goal_types) == 1 and goal_types[0].type == 'sale_goal' and \
                    goal_types[0].global_units:
                global_goal_types += goal_types[0]
                continue

            # Creo una línea por cada unidad operacional liquidada
            # aunque sea 0, (esto lo podríamos modificar)
            vals = {
                'settlement': self.id,
                'unit_id': op_unit.id,
                'name': _('Settlement in %s') % op_unit.name
            }
            ousl = self.env['operating.unit.settlement.line'].create(vals)

            # Añado a unit_info el coeficiente de las facturas y el objetivo
            # para esa unidad operacional, también para el cálculo global
            unit_info = invoices_by_unit[op_unit]
            total_coef = unit_info['coef'] / unit_info['num']
            amount_goal = month_goals.mapped('amount_goal')[0]
            unit_info.update({
                'amount_goal': amount_goal,
                'total_coef': total_coef
            })

            # Creo una goal.line por cada objetivo dentro de la linea de unidad
            # operacional:
            goal_line_vals = []
            for gt in goal_types:

                # Dejo para despues los tipos de objetivos que agrupan unidades
                if gt.type == 'sale_goal' and gt.global_units:
                    global_goal_types += gt
                    continue
                # Dejo para después los tipos de objetivos de mínimos de
                # clientes ya que el cálculo es global
                if (gt.type == 'min_customers'):
                    min_goal_types += gt
                    continue

                vals = self.get_sett_goal_line_vals(ousl, gt, unit_info)
                goal_line_vals.append((0, 0, vals))
            ousl.write({'goal_line_ids': goal_line_vals})

        # Líneas de liquidación por ventas marcadas como globales
        if len(global_goal_types) >= 1:
            self.create_extra_global_settlement_lines(global_goal_types,
                                                      invoices_by_global)

        # Líneas iquidación globales del tipo de objetivo de clinetes mínimos
        if len(min_goal_types) >= 1:
            self.create_extra_min_settlement_lines(min_goal_types,
                                                   invoices_by_unit)
        return

    def get_sett_goal_line_vals(self, ousl, gt, info_data):
        """
        Obtengo las líneas con los importes liquidados,
        Calculo las comisiones también con el porcentaje de señalamiento
        y devuelvo la liquidación sobre este importe,
        Si no hay señalamiento el porcentaje es el 100% (valor por defecto)
        y la liquidacion es la misma que la original.
        """
        vals = {}
        min_data = {}
        # Actualizo info si el tipo de objetivo es basado en mínimo de clientes
        if gt.type == 'min_customers':
            month_goal_obj = self.env['agent.month.goal']
            month = datetime.strptime(self.date_to, '%Y-%m-%d').month
            domain = [
                ('month', '=', month),
                ('agent_id', '=', self.agent.id),
            ]
            month_goals = month_goal_obj.search(domain)
            if not month_goals:
                return {}
            min_customers = month_goals.mapped('min_customers')[0]
            min_data = {
                'agent': self.agent,
                'date_from':  self.date_from,
                'date_to': self.date_to,
                'min_customers': min_customers,
                'month_goals': month_goals
            }

        commission, note = gt.get_commission(info_data, min_data)
        amount = 0.0
        reduced_amount = 0.0
        if 'amount' in info_data and 'reduced_amount' in info_data:
            amount = info_data['amount'] * (commission / 100.0)
            reduced_amount = info_data['reduced_amount'] * (commission / 100.0)
            note += _('\nSubtotal computed: %s') % info_data['amount']
            note += _('\nSubtotal reduced: %s') % info_data['reduced_amount']
        else:
            # En este caso info data esta agrupado por unidades
            total_amount = 0.0
            total_reduced_amount = 0.0
            for dic in info_data.values():
                total_amount += dic['amount']
                total_reduced_amount += dic['reduced_amount']
            amount = total_amount * (commission / 100.0)
            reduced_amount = total_reduced_amount * (commission / 100.0)
            note += _('\nSubtotal computed: %s') % amount
            note += _('\nSubtotal reduced: %s') % total_reduced_amount

        # Si hay calculo por señalamiento devuelvo la liquidacin reducida
        # settlement_amount = amount
        settlement_amount = reduced_amount or amount

        vals = {
            'unit_line_id': ousl.id,
            'goal_type_id': gt.id,
            'note': note,
            'commission': commission,
            'amount': settlement_amount
        }
        return vals

    def create_extra_min_settlement_lines(self, min_goal_types,
                                          invoices_by_unit):
        """
        """
        # import ipdb; ipdb.set_trace()
        vals = {
            'settlement': self.id,
            'unit_id': False,
            'name': _('Global settlement by min customers goal')
        }
        ousl = self.env['operating.unit.settlement.line'].create(vals)

        goal_line_vals = []
        for gt in min_goal_types:
            vals = self.get_sett_goal_line_vals(ousl, gt, invoices_by_unit)
            goal_line_vals.append((0, 0, vals))
        ousl.write({'goal_line_ids': goal_line_vals})
        return

    def create_extra_global_settlement_lines(self, global_goal_types,
                                             invoices_by_global):
        """
        Creo una línea extra, sin unidad operacional, que contenga,
        para cada tipo de objetivo de ventas marcado con unidades
        globales, una línea con el cálculo
        de objetivos globalmente, mirando el importe de todas las facturas
        y comparándolo con la suma de los objetivos de cada unidad 
        operacional
        """
        month_goal_obj = self.env['agent.month.goal']
        vals = {
            'settlement': self.id,
            'unit_id': False,
            'name': _('Global settlement by sales')
        }
        ousl = self.env['operating.unit.settlement.line'].create(vals)

        goal_line_vals = []
        month = datetime.strptime(self.date_to, '%Y-%m-%d').month
        for gt in global_goal_types:
            # Calculo el objetivo total del mes
            domain = [
                ('month', '=', month),
                ('agent_id', '=', self.agent.id),
                ('goal_type_id', '=', gt.id)
            ]
            month_goals = month_goal_obj.search(domain)
            if not month_goals:
                continue
            amount_goal = sum(month_goals.mapped('amount_goal'))
            invoices_by_global.update(amount_goal=amount_goal)

            vals = self.get_sett_goal_line_vals(ousl, gt, invoices_by_global)
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


class OperatingUnitSettlementLine(models.Model):
    _name = 'operating.unit.settlement.line'

    name = fields.Text('Description')
    settlement = fields.Many2one(
        "sale.commission.settlement", readonly=True, ondelete="cascade",
        required=True)
    unit_id = fields.Many2one(
        comodel_name='operating.unit', string='Operating Unit', required=False)
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
