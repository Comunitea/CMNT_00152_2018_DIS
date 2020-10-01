# Copyright 2020 Akretion France (http://www.akretion.com/)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
import logging

logger = logging.getLogger(__name__)


class StockValuationXlsx(models.TransientModel):
    _inherit = 'stock.valuation.xlsx'

    def compute_product_data(
            self, company_id, in_stock_product_ids, standard_price_past_date=False):
        self.ensure_one()

        logger.debug('Start compute_product_data')
        ppo = self.env['product.product']
        ppho = self.env['product.price.history']
        fields_list = self._prepare_product_fields()
        if not standard_price_past_date:
            fields_list.append('real_stock_cost')
        products = ppo.search_read([('id', 'in', in_stock_product_ids)], fields_list)
        product_id2data = {}
        for p in products:
            logger.debug('p=%d', p['id'])
            # I don't call the native method get_history_price()
            # because it requires a browse record and it is too slow
            if standard_price_past_date:
                history = ppho.search_read([
                    ('company_id', '=', company_id),
                    ('product_id', '=', p['id']),
                    ('datetime', '<=', standard_price_past_date)],
                    ['cost'], order='datetime desc, id desc', limit=1)
                standard_price = history and history[0]['cost'] or 0.0
            else:
                standard_price = p['real_stock_cost']
            product_id2data[p['id']] = {'standard_price': standard_price}
            for pfield in fields_list:
                if pfield.endswith('_id'):
                    product_id2data[p['id']][pfield] = p[pfield][0]
                else:
                    product_id2data[p['id']][pfield] = p[pfield]
        logger.debug('End compute_product_data')
        return product_id2data

