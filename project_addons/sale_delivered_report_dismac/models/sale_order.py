# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from datetime import datetime, timedelta
import dateutil.relativedelta


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_unreceived_sale_lines(self):
        tree_view = self.env.ref(
            'sale_delivered_report_dismac.view_delivery_report_tree')
        domain = [('product_id', '=', self.product_id.id)]
        return {
            'name': 'Sales delivery report',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.delivery.report',
            'views': [(tree_view.id, 'tree')],
            'domain': domain,
            'context': {'search_default_not_delivered': 1}
        }

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super().product_uom_change()
        #self._get_date_planned()
        return res

    def get_line_move(self, domain=[]):
        if not domain:
            domain = [('state', 'not in', ('cancel', 'done')), ('sale_line_id', '=', 'id'), ('location_dest_id.usage', '=', 'customer')]
        return self.env['stock.move'].search(domain, limit=1, order="id asc")

    @api.multi
    def _get_date_planned(self):
        ctx = self._context.copy()
        print ("Entro en _get_date_planned con contexcto {}".format(ctx))

        to_date = self._context.get('to_date', False)
        for line in self.filtered(lambda x:x.product_id and x.product_id.type=='product'):
            if not to_date:
                to_date = line.order_id.confirmation_date or fields.Datetime.now()
            print ("Buscando para fecha {}".format(to_date))
            ctx.update(product_id=line.product_id.id, to_date = to_date)

            # COmo puede haber entregas y cantidad cancelada, tendo en cuenta la cantidad pendiente, no la pedida
            qty_to_deliver = line.product_uom_qty - (line.qty_cancelled + line.qty_delivered)
            product = line.with_context(ctx).product_id
            sendable = False
            # Si hay stock en la fecha prevista.
            planned_delivery_date = False
            if qty_to_deliver <= product.virtual_available:
                line_move = line.get_line_move()
                if line_move:
                    planned_delivery_date = line.date_expected
                else:
                    planned_delivery_date = line.order_id.confirmation_date or fields.Datetime.now()
                sendable = True
            # Si no hay stock.
            elif qty_to_deliver > 0:
                sendable = False
                if line.id:
                    domain = [('product_id', '=', line.product_id.id), ('actual_status', 'in', ['in_progress', 'cancel'])]
                else:
                    domain = [('product_id', '=', line.product_id.id),
                              ('actual_status', 'in', ['in_progress', 'cancel'])]
                sl_report = self.with_context(ctx).env['sale.delivery.report'].search(domain).filtered(lambda x: x.date_order > line.order_id.date_order)
                if sl_report:
                    print('Lineas a considerar: {}'.format(sl_report))
                    print('Ultima: {}'.format(sl_report[0]))
                    planned_delivery_date =sl_report[0] and (sl_report[0].date_planned)
            #import ipdb;ipdb.set_trace()
            vals = {'sendable': sendable}
            if planned_delivery_date:
                planned_delivery_date = fields.Datetime.from_string(planned_delivery_date) + dateutil.relativedelta.relativedelta(days=line.product_id.sale_delay)
                vals.update(planned_delivery_date= fields.Datetime.to_string(planned_delivery_date))
            print ("Valores de la linea {}".format(vals))
            line.sendable = sendable
            line.planned_delivery_date = fields.Datetime.to_string(planned_delivery_date)

    planned_delivery_date = fields.Date("Estimated delivery date", compute="_get_date_planned")
    sendable = fields.Boolean("Sendable")
