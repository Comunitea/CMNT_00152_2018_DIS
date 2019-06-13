# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class GoalType(models.Model):
    _name = 'goal.type'

    name = fields.Char('Name', required=True)
    type = fields.Selection([
        ('sale_goal', 'Sale Goal'),
        ('margin_goal', 'Margin Goal'),
        ('min_customers', 'Min Customers'),
        ], 'Type', required=True)
    # BLOQUE 1 COMISIONES POR CENTAS
    by_sale_ids = fields.One2many(
        'commission.by.sales', 'goal_type_id', 'Sale Goal Rules')
    global_units = fields.Boolean(
        'Compute units globally', default=True)

    # BLOQUE 1 COMISIONES POR CENTAS
    by_margin_ids = fields.One2many(
        'commission.by.margin', 'goal_type_id', 'Margin Rules')

    # BLOQUE 3 DE COMISIONES POR MINIMO DE CLIENTES
    # Objetivo ventas mobiliario mes
    web_customers = fields.Integer('Nº new web customers')
    web_com = fields.Float('Commission (%)')

    # Objetivo ventas mobiliario mes
    mob_unit_id = fields.Many2one('operating.unit',
                                  'Forniture Operating Unit')
    mob_com = fields.Float('Commission (%)')

    # Objetivo ventas informatica mes
    info_unit_id = fields.Many2one('operating.unit',
                                   'Computing Operating Unit')
    info_com = fields.Float('Commission (%)')

    # Objetivo Nº Clientes
    num_customers = fields.Integer('Nº Customers with purchase')
    num_customers_com = fields.Float('Commission (%)')

    # Objetivo Nº nuevos clientes
    new_customers = fields.Integer('Nº new Customers')
    new_customers_com = fields.Float('Commission (%)')

    @api.multi
    def get_sale_goal_commission(self, info_data):
        """
        Si global_units es true, calculo los objetivos de todas las unidades
        operacionales, estén o no procesadas anteriormente.
        """

        commission = 0.0
        note = _('No Sale Goal Commission')

        amount_goal = round(info_data['amount_goal'], 2)
        amount = round(info_data['amount'], 2)

        if not amount_goal:
            return commission, note
        per = round((amount / amount_goal) * 100, 2)
        domain = [
            ('id', 'in', self.by_sale_ids.ids),
            ('goal_per', '<=', per),
        ]
        line = self.by_sale_ids.search(domain, order='goal_per desc', limit=1)
        if line:
            commission = line.commission
            note = ''
            note += _('Month goal: %s €\n') % amount_goal
            note += _('Computed amount: %s €\n') % amount
            note += _('Goal percentage: %s \n') % per
            note += _('Rule applied -> From percentage goal: %s') % \
                line.goal_per
        return commission, note

    @api.multi
    def get_margin_goal_commission(self, unit_info):
        commission = 0.0
        note = _('No Margin Commission')
        coef = unit_info['total_coef']
        domain = [
            ('id', 'in', self.by_margin_ids.ids),
            ('coef', '<=', coef),
        ]
        line = self.by_margin_ids.search(domain, order='coef desc', limit=1)
        if line:
            commission = line.commission
            note = _(
                'Computed coef: %s \n'
                'Rule applied -> From Margin Coeff %s'
            ) % (coef, line.coef)
        return commission, note

    def get_web_commission(self, units_info, min_data):
        commission = 0.0
        note = _('No Web Commission')

        so = self.env['sale.order']
        # Comprobar número de clientes con compra por web
        orders = min_data.get('orders')
        web_orders = orders.filtered(
            lambda x: x.team_id.team_type == 'web_site')
        web_customers = web_orders.mapped('partner_id')
        new_web_customers = 0
        # Contar los clientes que no tienen ventas anteriores
        for customer in web_customers:
            domain = [
                ('partner_id', '=', customer.id),
                ('date_order', '<', min_data['date_from']),
                ('state', 'not in', ['draft, cancell'])
            ]
            old_orders = so.search(domain)
            if not old_orders:
                new_web_customers += 1
        if new_web_customers >= self.web_customers:
            commission = self.web_com
            note = _(
                'WEB SALE COMMISSION\n'
                'Goal web customers: %s\n'
                'Num web customers: %s\n'
                'Commission applied: %s %'
            ) % (self.web_customers, new_web_customers, commission)
        return commission, note

    def get_mob_commission(self, units_info, min_data):
        commission = 0.0
        note = _('No Forniture Commission')
        if self.mob_unit_id and units_info.get(self.mob_unit_id, {}):
            mob_data = units_info.get(self.mob_unit_id)
            if mob_data['amount'] >= mob_data['amount_goal']:
                commission = self.mob_com
                note = _(
                   'FORNITURE COMMISSION\n'
                   'amount goal : %s \n'
                   'goal : %s \n'
                   'Commission applied: %s'
                ) % (mob_data['amount_goal'], mob_data['amount'], commission)
        return commission, note

    def get_inf_commission(self, units_info, min_data):
        commission = 0.0
        note = _('No Computing Commission')
        if self.info_unit_id and units_info.get(self.info_unit_id, {}):
            info_data = units_info.get(self.mob_unit_id)
            if info_data['amount'] >= info_data['amount_goal']:
                commission = self.minfo_om
                note = _(
                    'COMPUTING COMMISSION\n'
                    'amount goal : %s \n'
                    'amount : %s \n'
                    'Commission applied: %s'
                ) % (info_data['amount_goal'], info_data['amount'], commission)
        return commission, note

    def get_num_customers_commission(self, units_info, min_data):
        commission = 0.0
        note = _('No Num Customers Commission')
        orders = min_data.get('orders')
        customers = orders.mapped('partner_id')
        num_customers = len(customers)
        if num_customers >= self.num_customers:
            commission = self.num_customers_com
            note = _(
                'Nº CUSTOMERS COMMISSION\n'
                'Goal customer numbers : %s \n'
                'number : %s \n'
                'Commission applied: %s'
            ) % (self.num_customers, num_customers, commission)
        return commission, note

    def get_new_customers_commission(self, units_info, min_data):
        commission = 0.0
        note = _('No New Customers Commission')
        so = self.env['sale.order']
        # Comprobar número de clientes con compra por web
        orders = min_data.get('orders')

        order_customers = orders.mapped('partner_id')
        new_customers = 0
        # Contar los clientes que no tienen ventas anteriores
        # siendo ventas inferiores dos ños atras
        for customer in order_customers:
            two_years_ago = datetime.now() - relativedelta(years=2)
            two_years_ago_date = two_years_ago.strftime('%Y-%m-%d')
            domain = [
                ('partner_id', '=', customer.id),
                ('date_order', '<', min_data['date_from']),
                ('date_order', '>', two_years_ago_date),
                ('state', 'not in', ['draft, cancell'])
            ]
            old_orders = so.search(domain)
            if not old_orders:
                new_customers += 1
        if new_customers >= self.new_customers:
            commission = self.new_customers_com
            note = _(
                'NEW CUSTOMERS COMMISSION\n'
                'Goal Num new customers: %s \n'
                'Num new Customers: %s \n'
                'Commission applied: %s'
            ) % (self.new_customers, new_customers, commission)
        return commission, note

    @api.multi
    def get_min_customers_commission(self, units_info, min_data={}):
        """
        En esta función, units_info es la agrupación por unidades con
        toda la info necesaria para el cálculo de comisión en lugar
        de directamente la info de una unidad concreta.
        """

        commission = 0.0
        note = _('No Min customers Commission')
        # Compruebo número de clientes de este mes
        so = self.env['sale.order']
        agent = min_data['agent']
        agent_user = self.env['res.users'].search(
            [('partner_id', '=', agent.id)])
        if not agent_user:
            raise UserError(_('No user related to agent %s') % agent.name)
        domain = [
            ('user_id', '=', agent_user.id),
            ('date_order', '>=', min_data['date_from']),
            ('date_order', '<=', min_data['date_to']),
            ('state', 'not in', ['draft', 'cancell'])
        ]
        orders = so.search(domain)
        customers = orders.mapped('partner_id')
        min_data.update(orders=orders)
        if customers and len(customers) >= min_data['min_customers']:
            note = '----------------------------------------------------\n'
            sep = '\n----------------------------------------------------\n'
            # Calculo comisiones por ventas web
            com2, note2 = self.get_web_commission(units_info, min_data)
            commission += com2
            note += note2 + sep

            # Calculo comision por ventas mobiliario
            com2, note2 = self.get_mob_commission(units_info, min_data)
            commission += com2
            note += sep + note2 + sep

            # Calculo comision por ventas informatica
            com2, note2 = self.get_inf_commission(units_info, min_data)
            commission += com2
            note += sep + note2 + sep

            # Calculo nº clientes con compra
            com2, note2 = self.get_num_customers_commission(units_info,
                                                            min_data)
            commission += com2
            note += sep + note2 + sep

            # Calculo nuevos clientes
            com2, note2 = self.get_new_customers_commission(units_info,
                                                            min_data)
            commission += com2
            note += sep + note2 + sep
        return commission, note

    @api.multi
    def get_commission(self, unit_info,  min_data={}):
        self.ensure_one()
        commission = 0.0
        note = ''
        if self.type == 'sale_goal':
            commission, note = self.get_sale_goal_commission(unit_info)
        elif self.type == 'margin_goal':
            commission, note = self.get_margin_goal_commission(unit_info)
        elif self.type == 'min_customers':
            commission, note = \
                self.get_min_customers_commission(unit_info, min_data)
        return commission, note


class CommissionBySales(models.Model):

    _name = 'commission.by.sales'

    goal_type_id = fields.Many2one(
        comodel_name='goal.type', string='Goal Type', required=True)
    goal_per = fields.Float('From % Goal', required=True)
    commission = fields.Float('Commission (%)')


class CommissionByMargin(models.Model):

    _name = 'commission.by.margin'

    goal_type_id = fields.Many2one(
        comodel_name='goal.type', string='Type', required=True)
    coef = fields.Float('From Margin Coeff', required=True)
    commission = fields.Float('Commission (%)')
