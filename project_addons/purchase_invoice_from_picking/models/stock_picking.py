# © 2019 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv.expression import AND


def _get_formatted_picking_name(picking):
    name = picking.name

    if picking.supplier_ref:
        name = '{} - {}'.format(name, picking.supplier_ref)

    if picking.origin:
        name = '{} ({})'.format(name, picking.origin)

    return name


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    # supplier_reference = fields.Char(
    #     copy=False, index=True,
    #     track_visibility='onchange',
    # )


    show_supplier_reference = fields.Boolean(compute='_compute_show_supplier_reference')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        res = super().name_search(name, args, operator, limit)

        # The module only supports positive operators.
        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
        if operator not in positive_operators:
            return res

        if name and limit is None or len(res) < limit:
            ids_already_found = [r[0] for r in res]
            remaining_limit = None if limit is None else limit - len(res)

            domain = AND(((args or []), [
                '&',
                ('id', 'not in', ids_already_found),
                '|',
                ('supplier_ref', operator, name),
                ('origin', operator, name),
            ]))

            pickings_with_supplier_reference = self.search(domain, limit=remaining_limit)

            res += pickings_with_supplier_reference.name_get()

        return res

    def name_get(self):
        """Show the supplier reference in the name of the picking.

        The context variable is used to have a specific format for picking names when
        selecting a picking for a supplier invoice.
        """
        if self._context.get('show_picking_supplier_reference'):
            return [(p.id, _get_formatted_picking_name(p)) for p in self]
        else:
            return super().name_get()

    @api.depends('location_id')
    def _compute_show_supplier_reference(self):
        for picking in self:
            picking.show_supplier_reference = picking.location_id.usage == 'supplier'



class StockMove(models.Model):

    _inherit = 'stock.move'


    purchase_price_subtotal = fields.Monetary(
        compute='_compute_purchase_order_line_fields',
        string='Price subtotal',
        compute_sudo=True,
    )
    purchase_price_total = fields.Monetary(
        compute='_compute_purchase_order_line_fields',
        string='Price total',
        compute_sudo=True,
    )
    currency_id = fields.Many2one('res.currency',
                                  related='purchase_line_id.currency_id',
                                  readonly=True)
    purchase_tax_id = fields.Many2many(
        related='purchase_line_id.taxes_id', readonly=True,
        string='Sale Tax',
    )

    @api.multi
    def _compute_purchase_order_line_fields(self):
        """This is computed with sudo for avoiding problems if you don't have
        access to purchase orders (stricter warehouse users, inter-company
        records...).
        """
        for line in self:
            purchase_line = line.purchase_line_id
            price_unit = (
                purchase_line.price_subtotal / purchase_line.product_uom_qty
                if purchase_line.product_uom_qty else purchase_line.price_reduce)
            taxes = line.purchase_tax_id.compute_all(
                price_unit=price_unit,
                currency=purchase_line.currency_id,
                quantity=line.quantity_done or line.product_uom_qty,
                product=line.product_id,
                partner=purchase_line.order_id.partner_id)
            
            #price_tax = taxes['total_included'] - taxes['total_excluded']
            line.update({
                'purchase_price_subtotal': taxes['total_excluded'],
                'purchase_price_total': taxes['total_included'],
                })