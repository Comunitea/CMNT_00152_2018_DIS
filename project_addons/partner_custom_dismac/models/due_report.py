# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class DueReport(models.Model):
    _name = "due.report"
    _description = "Due Report"
    _auto = False
    _order = 'date_maturity asc'

    @api.model
    def _get_done_states(self):
        return ['sale', 'done', 'paid']


    date_maturity = fields.Date('Maturity Date', readonly=True)
    date_invoice = fields.Date('Invoice Date', readonly=True)
    residual = fields.Float('Amount', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    invoice_id = fields.Many2one('account.invoice', 'Invoice', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    
    
    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            aml.id as id,
            aml.partner_id as partner_id,
            aml.invoice_id as invoice_id, 
            aml.amount_residual as residual, 
            aml.date_maturity as date_maturity, 
            ai.date_invoice as date_invoice, 
            ai.user_id as user_id 
        """

        for field in fields.values():
            select_ += field

        from_ = """
                account_move_line aml
                INNER JOIN account_account aa ON aml.account_id = aa.id
                LEFT JOIN account_invoice ai ON ai.id = aml.invoice_id  
                %s
        """ % from_clause

        groupby_ = " "

        return "%s SELECT %s FROM %s WHERE aa.internal_type in ('receivable') and aml.reconciled = False" % (with_, select_, from_)

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        print(self._query())
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

