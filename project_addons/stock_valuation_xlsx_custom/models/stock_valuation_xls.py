# Copyright 2020 Akretion France (http://www.akretion.com/)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_round
from io import BytesIO
from datetime import datetime
import xlsxwriter
import logging
import base64


logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    @api.depends('categ_id')
    def compute_familiy_id(self):
        for product in self:
            product.parent_categ_id = product.categ_id.parent_id

    parent_categ_id = fields.Many2one('product.category', string="Familia", compute="compute_familiy_id", store=True)


class StockValuationXlsx(models.TransientModel):
    _inherit = 'stock.valuation.xlsx'

    def stringify_and_sort_result(
            self, product_ids, product_id2data, data,
            prec_qty, prec_price, prec_cur_rounding, categ_id2name,
            uom_id2name, lot_id2data, loc_id2name, categ_2_id2name):
        logger.debug('Start stringify_and_sort_result')
        res = []
        for l in data:
            product_id = l['product_id']
            qty = float_round(l['qty'], precision_digits=prec_qty)
            standard_price = float_round(
                product_id2data[product_id]['standard_price'],
                precision_digits=prec_price)
            subtotal = float_round(
                standard_price * qty, precision_rounding=prec_cur_rounding)
            res.append(dict(
                product_id2data[product_id],
                product_name=product_id2data[product_id]['name'],
                loc_name=l['location_id'] and loc_id2name[l['location_id']] or '',
                lot_name=l['lot_id'] and lot_id2data[l['lot_id']]['name'] or '',
                expiry_date=l['lot_id'] and lot_id2data[l['lot_id']].get('expiry_date'),
                qty=qty,
                uom_name=uom_id2name[product_id2data[product_id]['uom_id']],
                standard_price=standard_price,
                subtotal=subtotal,
                categ_name=categ_id2name[product_id2data[product_id]['parent_categ_id']],
                categ2_name = categ_2_id2name[product_id2data[product_id]['categ_id']],
                ))
        sort_res = sorted(res, key=lambda x: x['product_name'])
        logger.debug('End stringify_and_sort_result')
        return sort_res

    def id2name(self, product_ids):
        logger.debug('Start id2name')
        pco = self.env['product.category']
        splo = self.env['stock.production.lot']
        slo = self.env['stock.location'].with_context(active_test=False)
        puo = self.env['uom.uom'].with_context(active_test=False)
        categ_id2name = {}
        categ_2_id2name = {}
        categ_domain = []
        if self.categ_ids:
            categ_domain = [('id', 'child_of', self.categ_ids.ids)]
        for categ in pco.search(categ_domain):
            categ_id2name[categ.parent_id.id] = categ.parent_id.name
            categ_2_id2name[categ['id']] = categ.name

        uom_id2name = {}
        uoms = puo.search_read([], ['name'])
        for uom in uoms:
            uom_id2name[uom['id']] = uom['name']
        lot_id2data = {}
        lot_fields = ['name']
        if hasattr(splo, 'expiry_date'):
            lot_fields.append('expiry_date')

        lots = splo.search_read(
            [('product_id', 'in', product_ids)], lot_fields)
        for lot in lots:
            lot_id2data[lot['id']] = lot
        loc_id2name = {}
        locs = slo.search_read(
            [('id', 'child_of', self.location_id.id)], ['display_name'])
        for loc in locs:
            loc_id2name[loc['id']] = loc['display_name']
        logger.debug('End id2name')
        return categ_id2name, uom_id2name, lot_id2data, loc_id2name,categ_2_id2name

    def _prepare_cols(self):
        cols = {
            'default_code': {'width': 18, 'style': 'regular', 'sequence': 10, 'title': _('Product Code')},
            'product_name': {'width': 60, 'style': 'regular', 'sequence': 20, 'title': _('Product Name')},
            'loc_name': {'width': 14, 'style': 'regular', 'sequence': 30, 'title': _('Location Name')},
            'lot_name': {'width': 14, 'style': 'regular', 'sequence': 40, 'title': _('Lot')},
            'expiry_date': {'width': 14, 'style': 'regular_date', 'sequence': 50, 'title': _('Expiry Date'),
                            'type': 'date'},
            'qty': {'width': 8, 'style': 'regular', 'sequence': 60, 'title': _('Qty')},
            'uom_name': {'width': 8, 'style': 'regular_small', 'sequence': 70, 'title': _('UoM')},
            'standard_price': {'width': 14, 'style': 'regular_price_currency', 'sequence': 80,
                               'title': _('Coste')},
            'subtotal': {'width': 14, 'style': 'regular_currency', 'sequence': 90, 'title': _('€ Artículo'),
                         'formula': True},
            'categ_subtotal': {'width': 14, 'style': 'regular_currency', 'sequence': 100, 'title': _('€ Familia'),
                               'formula': True},
            'categ_name': {'width': 20 , 'style': 'regular', 'sequence': 110, 'title': _('Familia')},
            'categ2_name': {'width': 20, 'style': 'regular_small', 'sequence': 120, 'title': _('Categoría')}
        }
        return cols

    def compute_product_data(
            self, company_id, in_stock_product_ids, standard_price_past_date=False):
        ##Lo heredo todo porque el campo de coste a utilizar es otro  standard_price = p['real_stock_cost']
        self.ensure_one()
        logger.debug('Start compute_product_data')
        ppo = self.env['product.product']
        ppho = self.env['product.price.history']
        fields_list = self._prepare_product_fields()
        if not standard_price_past_date:
            fields_list.append('real_stock_cost')
            fields_list.append('standard_price')
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
                standard_price = p['real_stock_cost'] or 0.0
            if not standard_price:
                standard_price = p['standard_price']
            product_id2data[p['id']] = {'standard_price': standard_price}
            for pfield in fields_list:
                if pfield.endswith('_id'):
                    product_id2data[p['id']][pfield] = p[pfield][0]
                else:
                    product_id2data[p['id']][pfield] = p[pfield]
        logger.debug('End compute_product_data')
        return product_id2data

    def _prepare_product_fields(self):
        return ['uom_id', 'name', 'default_code', 'categ_id', 'parent_categ_id']

    def generate(self):
        self.ensure_one()
        logger.debug('Start generate XLSX stock valuation report')
        splo = self.env['stock.production.lot'].with_context(active_test=False)
        prec_qty = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        prec_price = self.env['decimal.precision'].precision_get('Product Price')
        company = self.env.user.company_id
        company_id = company.id
        prec_cur_rounding = company.currency_id.rounding
        self._check_config(company_id)

        product_ids = self.get_product_ids()
        if not product_ids:
            raise UserError(_("There are no products to analyse."))
        split_by_lot = self.split_by_lot
        split_by_location = self.split_by_location
        if self.source == 'stock':
            if self.stock_date_type == 'present':
                past_date = False
                data, in_stock_products = self.compute_data_from_present_stock(
                    company_id, product_ids, prec_qty)
            elif self.stock_date_type == 'past':
                split_by_lot = False
                split_by_location = False
                past_date = self.past_date
                data, in_stock_products = self.compute_data_from_past_stock(
                    product_ids, prec_qty, past_date)
        elif self.source == 'inventory':
            past_date = self.inventory_id.date
            data, in_stock_products = self.compute_data_from_inventory(product_ids, prec_qty)
        standard_price_past_date = past_date
        if not (self.source == 'stock' and self.stock_date_type == 'present') and self.standard_price_date == 'present':
            standard_price_past_date = False
        in_stock_product_ids = list(in_stock_products.keys())
        product_id2data = self.compute_product_data(
            company_id, in_stock_product_ids,
            standard_price_past_date=standard_price_past_date)
        data_res = self.group_result(data, split_by_lot, split_by_location)
        categ_id2name, uom_id2name, lot_id2data, loc_id2name, categ_2_id2name = self.id2name(product_ids)
        res = self.stringify_and_sort_result(
            product_ids, product_id2data, data_res, prec_qty, prec_price, prec_cur_rounding,
            categ_id2name, uom_id2name, lot_id2data, loc_id2name, categ_2_id2name)

        logger.debug('Start create XLSX workbook')
        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        sheet = workbook.add_worksheet('Stock')
        styles = self._prepare_styles(workbook, company, prec_price)
        cols = self._prepare_cols()
        categ_subtotal = self.categ_subtotal
        # remove cols that we won't use
        if not split_by_lot:
            cols.pop('lot_name', None)
            cols.pop('expiry_date', None)
        if not hasattr(splo, 'expiry_date'):
            cols.pop('expiry_date', None)
        if not split_by_location:
            cols.pop('loc_name', None)
        if not categ_subtotal:
            cols.pop('categ_subtotal', None)

        j = 0
        for col, col_vals in sorted(cols.items(), key=lambda x: x[1]['sequence']):
            cols[col]['pos'] = j
            cols[col]['pos_letter'] = chr(j + 97).upper()
            sheet.set_column(j, j, cols[col]['width'])
            j += 1

        # HEADER
        now_dt = fields.Datetime.context_timestamp(self, datetime.now())
        now_str = fields.Datetime.to_string(now_dt)
        if past_date:
            stock_time_utc_dt = past_date
            stock_time_dt = fields.Datetime.context_timestamp(self, stock_time_utc_dt)
            stock_time_str = fields.Datetime.to_string(stock_time_dt)
        else:
            stock_time_str = now_str
        if standard_price_past_date:
            standard_price_date_str = stock_time_str
        else:
            standard_price_date_str = now_str
        i = 0
        sheet.write(i, 0, 'Odoo - Valoración de stock', styles['doc_title'])
        sheet.set_row(0, 26)
        i += 1
        #sheet.write(i, 0, 'Fecha: %s' % stock_time_str, styles['doc_subtitle'])
        #i += 1
        sheet.write(i, 0, 'Fecha (coste): %s' % standard_price_date_str, styles['doc_subtitle'])
        i += 1
        sheet.write(i, 0, 'Ubicación: %s' % self.location_id.name,
                    styles['doc_subtitle'])
        if self.categ_ids:
            i += 1
            sheet.write(i, 0, 'Familia/Categorías: %s' % ', '.join([categ.display_name for categ in self.categ_ids]),
                        styles['doc_subtitle'])
        i += 1
        sheet.write(i, 0, 'Creado el %s por %s' % (now_str, self.env.user.name), styles['regular_small'])

        # TITLE of COLS
        i += 2
        for col in cols.values():
            sheet.write(i, col['pos'], col['title'], styles['col_title'])

        i += 1
        sheet.write(i, cols['subtotal']['pos'] - 1, _("TOTAL:"), styles['total_title'])
        total_row = i

        # LINES
        if categ_subtotal:
            categ_ids = categ_id2name.keys()
        else:
            categ_ids = [0]

        total = 0.0
        letter_qty = cols['qty']['pos_letter']
        letter_price = cols['standard_price']['pos_letter']
        letter_subtotal = cols['subtotal']['pos_letter']
        crow = 0
        lines = res
        for categ_id in categ_ids:
            ctotal = 0.0
            categ_has_line = False
            if categ_subtotal:
                # skip a line and save it's position as crow
                i += 1
                crow = i
                lines = filter(lambda x: x['parent_categ_id'] == categ_id, res)
            for l in lines:
                i += 1
                total += l['subtotal']
                ctotal += l['subtotal']
                categ_has_line = True
                subtotal_formula = '=%s%d*%s%d' % (letter_qty, i + 1, letter_price, i + 1)
                sheet.write_formula(i, cols['subtotal']['pos'], subtotal_formula, styles['regular_currency'],
                                    l['subtotal'])
                for col_name, col in cols.items():
                    if not col.get('formula'):
                        if col.get('type') == 'date' and l[col_name]:
                            l[col_name] = fields.Date.from_string(l[col_name])
                        sheet.write(i, col['pos'], l[col_name], styles[col['style']])
            if categ_subtotal:
                if categ_has_line:
                    sheet.write(crow, 0, categ_id2name[categ_id], styles['categ_title'])
                    for x in range(cols['categ_subtotal']['pos'] - 1):
                        sheet.write(crow, x + 1, '', styles['categ_title'])

                    cformula = '=SUM(%s%d:%s%d)' % (letter_subtotal, crow + 2, letter_subtotal, i + 1)
                    sheet.write_formula(crow, cols['categ_subtotal']['pos'], cformula, styles['categ_currency'],
                                        float_round(ctotal, precision_rounding=prec_cur_rounding))
                else:
                    i -= 1  # go back to skipped line

        # Write total
        total_formula = '=SUM(%s%d:%s%d)' % (letter_subtotal, total_row + 2, letter_subtotal, i + 1)
        sheet.write_formula(total_row, cols['subtotal']['pos'], total_formula, styles['total_currency'],
                            float_round(total, precision_rounding=prec_cur_rounding))

        workbook.close()
        logger.debug('End create XLSX workbook')
        file_data.seek(0)
        filename = 'Odoo_stock_%s.xlsx' % stock_time_str.replace(' ', '-').replace(':', '_')
        export_file_b64 = base64.b64encode(file_data.read())
        self.write({
            'state': 'done',
            'export_filename': filename,
            'export_file': export_file_b64,
        })
        # action = {
        #    'name': _('Stock Valuation XLSX'),
        #    'type': 'ir.actions.act_url',
        #    'url': "web/content/?model=%s&id=%d&filename_field=export_filename&"
        #           "field=export_file&download=true&filename=%s" % (
        #               self._name, self.id, self.export_filename),
        #    'target': 'self',
        #    }
        action = self.env['ir.actions.act_window'].for_xml_id(
            'stock_valuation_xlsx', 'stock_valuation_xlsx_action')
        action['res_id'] = self.id
        return action