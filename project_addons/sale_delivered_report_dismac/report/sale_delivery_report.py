# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import tools
from odoo import api, fields, models
from lxml import etree
from odoo.addons import decimal_precision as dp


class SaleDelivery(models.Model):
    _name = "sale.delivery.report"
    _description = "Sales Delivery Status"
    _auto = False
    _rec_name = "date_order"
    _order = "date_order asc"

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="tree", toolbar=False, submenu=False
    ):

        ctx = self._context
        res = super(SaleDelivery, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == "form" and ctx.get("product_id", False):
            doc = etree.XML(res["arch"])
            for node in doc.xpath("//field[@class='hide_product_id']"):
                node.set("invisible", "0")
            res["arch"] = etree.tostring(doc)
        return res

    @api.multi
    def _get_sl_from(self):
        sl_from = self._context.get("sale_order_line_id", False)
        sl_from = self.env["sale.order.line"].browse(sl_from)
        for sr in self:
            sr.sl_from = sl_from

    @api.multi
    def _get_purchase_order_line(self):
        pol_ids = self.env["purchase.order.line"]
        for line in self:
            domain = [
                ("product_id", "=", line.product_id.id),
                ("qty_to_receive", "!=", 0),
                ("date_planned", "<=", line.date_order),
                ("id", "not in", pol_ids.ids),
            ]
            pol = self.env["purchase.order.line"].search(
                domain, order="date_planned asc", limit=1
            )
            if pol:
                pol_ids |= pol
                line.purchase_order_line_id.id = pol.id

    def get_sale_order_line(self, product_id, sale_order_line_id):
        line = self.filtered(
            lambda x: x.sl_from == sale_order_line_id
            and x.product_id == product_id
        )
        return line and line.date_planned

    @api.multi
    def get_p_line_qty_available(self, qty=0.00, to_date=False):
        qties = []
        for line in self:

            to_date = max(to_date or line.date_expected, fields.Datetime.now())
            qties = line.product_id._compute_quantities_dict(
                self._context.get("lot_id"),
                self._context.get("owner_id"),
                self._context.get("package_id"),
                self._context.get("from_date"),
                to_date=to_date,
            )
            if qties[line.product_id.id]["virtual_available"] >= qty:
                return line
        return False

    @api.multi
    def _get_line_qty_available(self, to_date=False):
        vals = {}
        for line in self:
            to_date = line.date_order
            qties = line.product_id._compute_quantities_dict(
                self._context.get("lot_id"),
                self._context.get("owner_id"),
                self._context.get("package_id"),
                self._context.get("from_date"),
                to_date=to_date,
            )

            line.line_virtual_available = qties[line.product_id.id][
                "virtual_available"
            ]
            line.line_qty_available = qties[line.product_id.id]["qty_available"]
        return

    @api.multi
    def _get_qty_to_delivered(self, product_id=False):

        # product_id = self.mapped('product_id')
        if not product_id or len(product_id) != 1:
            p_id = self._context.get("product_id", False) or self._context.get(
                "line_product_id", False
            )
            product_id = self.env["product.product"].browse(p_id)
        if not product_id:
            return
        # Compras asociadas pendientes de recibir
        # domain = [('product_id', '=', product_id.id), ('qty_to_receive', '!=', 0)]
        # pol = self.env['purchase.order.line'].search(domain, order='date_planned asc')
        # Movimientos de entrada de compras asociados a este producto

        domain = [
            ("product_id", "=", product_id.id),
            ("location_id.usage", "=", "supplier"),
            ("purchase_line_id", "!=", False),
            ("state", "not in", ("done", "cancel", "draft")),
        ]

        p_moves = self.env["stock.move"].search(
            domain, order="date_expected asc"
        )
        stock_qty = qty_available = product_id.qty_available
        qty_reserved = 0.00

        lines = self.filtered(lambda x: x.product_id == product_id).sorted(
            key="date_order", reverse=False
        )
        purchases = lines.filtered(lambda x: x.purchase_order_id).sorted(
            key="date_expected", reverse=False
        )

        if lines:
            max_date = lines[0].date_expected
        last={}
        for line in lines:
            product_uom_qty = line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_uom
            )
            qty_cancelled = line.product_uom._compute_quantity(
                line.qty_cancelled, line.product_uom
            )
            qty_delivered = line.product_uom._compute_quantity(
                line.qty_delivered, line.product_uom
            )

            line.qty_available_to_delivered = qty_available
            line.qty_to_delivered = (
                product_uom_qty - qty_delivered - qty_cancelled
            )

            max_date = max(max_date, line.date_expected)

            if line.purchase_order_id:

                line.date_available = line.date_expected
                line.date_planned = line.date_expected

                qty_available += line.qty_to_delivered
                line.qty_available_after_delivered = qty_available
                line.qty_available_to_delivered = line.qty_to_delivered
                line.qty_to_receive = line.qty_to_delivered
                line.purchase_order_ids = [(6, 0, [line.purchase_order_id.id])]

                line.sendable = True
                line.purchase_order_group = "Purchase"
                purchases = purchases - line
                last = {
                    "qty": qty_available,
                    "date": line.date_expected,
                    "id": line.purchase_order_id.id,
                }

                continue

            if line.sale_order_id:
                qty_reserved += line.qty_to_delivered
                from_initial_stock = qty_reserved <= stock_qty

                from_stock = qty_available >= line.qty_to_delivered
                # Si me llega lo que hay
                if from_stock:
                    line.qty_available_to_delivered = qty_available
                    qty_available -= line.qty_to_delivered
                    line.qty_available_after_delivered = qty_available
                    qty_reserved += line.qty_to_delivered
                    if from_initial_stock:
                        line.date_available = line.date_expected
                        line.purchase_order_group = "Stock"
                        line.sendable = True
                        # line.date_planned = line.date_expected
                    else:
                        if last:
                            line.date_available = last["date"]
                            line.purchase_order_group = "Order"
                            line.sendable = True
                            # line.date_planned = last['date']
                            line.purchase_order_ids = [(6, 0, [last["id"]])]

                    # NO me llega lo que hay, busco la primera compra y añado los campos
                    # date_planned, purchase_order_ids y purchase_group
                else:

                    purchase_line = purchases.get_p_line_qty_available(
                        qty=line.qty_to_delivered
                    )
                    if purchase_line:
                        line.date_available = purchase_line.date_expected
                        line.sendable = True
                        line.purchase_order_group = "Order"
                        line.purchase_order_ids = [
                            (6, 0, [purchase_line.purchase_order_id.id])
                        ]
                    else:
                        line.date_available = False
                        line.sendable = False
                        line.purchase_order_group = "No Stock"

                    qty_available -= line.qty_to_delivered
                    line.qty_available_after_delivered = qty_available
                    qty_reserved += line.qty_to_delivered
            line.date_planned = (
                line.date_expected or line.date_order
            )  # max(line.date_available or line.date_order, line.date_order or line.date_available)
            if not line.purchase_order_id and not line.sale_order_id:
                line.purchase_order_group = "Move"

        self = lines.sorted(
            key=lambda x: (x.date_available or max_date, x.sale_order_line_id)
        )

    @api.model
    def default_get(self, fields):
        return super().default_get(fields)

    @api.multi
    def get_name(self):
        for line in self:
            if line.sale_order_id:
                order = "{}.{}".format(
                    line.sale_order_id.name, line.sale_order_line_id.id
                )
            else:
                order = "{}.{}".format(
                    line.purchase_order_id.name, line.purchase_order_line_id.id
                )
            line.name = "{} {} {}".format(
                order, line.product_uom_qty, line.date_expected
            )

    name = fields.Char(compute="get_name")
    product_id = fields.Many2one("product.product", readonly=True)
    partner_id = fields.Many2one("res.partner", readonly=True)
    sale_order_id = fields.Many2one("sale.order", readonly=True)
    purchase_order_id = fields.Many2one("purchase.order", readonly=True)

    sale_order_line_id = fields.Many2one("sale.order.line", readonly=True)
    purchase_order_line_id = fields.Many2one("purchase.order.line")

    # stock_move_id = fields.Many2one('stock.move', readonly=True)
    purchase_order_ids = fields.Many2many(
        "purchase.order", compute="_get_qty_to_delivered"
    )
    product_uom_qty = fields.Float(
        "Qty Ordered",
        readonly=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    product_uom = fields.Many2one(
        "uom.uom", string="Product Unit of Measure", required=True
    )
    qty_delivered = fields.Float(
        related="sale_order_line_id.qty_delivered", readonly=True
    )
    qty_cancelled = fields.Float(
        "Qty Canceled",
        readonly=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    qty_available = fields.Float(
        related="product_id.qty_available", readonly=True
    )
    qty_to_receive = fields.Float(
        compute="_get_qty_to_delivered",
        digits=dp.get_precision("Product Unit of Measure"),
    )
    qty_reserved = fields.Float(
        compute="_get_qty_to_delivered",
        digits=dp.get_precision("Product Unit of Measure"),
    )
    qty_to_delivered = fields.Float(
        compute="_get_qty_to_delivered",
        digits=dp.get_precision("Product Unit of Measure"),
    )
    qty_available_to_delivered = fields.Float(
        compute="_get_qty_to_delivered",
        digits=dp.get_precision("Product Unit of Measure"),
    )
    qty_available_after_delivered = fields.Float(
        compute="_get_qty_to_delivered",
        digits=dp.get_precision("Product Unit of Measure"),
    )
    sendable = fields.Float(compute="_get_qty_to_delivered")
    sl_from = fields.Many2one(
        "sale.order.line", readonly=True, compute="_get_sl_from"
    )
    purchase_order_group = fields.Char(
        "Purchase group", compute="_get_qty_to_delivered"
    )

    actual_status = fields.Selection(
        selection=[
            ("in_progress", "En proceso"),
            ("sent", "Enviado"),
            ("cancel", "Cancelado"),
        ],
        readonly=True,
    )

    sm_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("waiting", "Waiting Another Operation"),
            ("confirmed", "Waiting"),
            ("partially_available", "Partially Available"),
            ("assigned", "Ready"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft Quotation"),
            ("sent", "Quotation Sent"),
            ("sale", "Sales Order"),
            ("purchase", "Purchase Order"),
            ("done", "Order Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
    )

    line_virtual_available = fields.Float(
        "Forecast Quantity",
        compute="_get_line_qty_available",
        digits=dp.get_precision("Product Unit of Measure"),
    )
    line_qty_available = fields.Float(
        "Quantity On Hand",
        compute="_get_line_qty_available",
        digits=dp.get_precision("Product Unit of Measure"),
    )

    date_order = fields.Datetime(readonly=True, help="Order date.")
    date_planned = fields.Datetime(compute="_get_qty_to_delivered")
    date_expected = fields.Datetime(
        readonly=True,
        help="Move date. If no moves:\n Requested date in sales or Date planned in purchases",
    )
    date_available = fields.Datetime(
        compute="_get_qty_to_delivered",
        readonly=True,
        help="Data with available stock",
    )

    def _select(self):
        select_str = """
             SELECT
                    min(l.id) as id,
                    l.id as sale_order_line_id,
                    null as purchase_order_line_id,
                    l.product_id as product_id,
                    l.order_id as sale_order_id,
                    null as purchase_order_id,
                    s.date_order,
                    s.state,
                    sm.state as sm_state,
                    s.partner_id as partner_id,
                    l.product_uom_qty as product_uom_qty,
                    l.product_uom,
                    l.qty_delivered as qty_delivered,
                    l.qty_cancelled as qty_cancelled,
                    case
                        when sm.state in ('done', 'cancel') then sm.date
                        else sm.date_expected
                    end as date_expected,
                    case
                        when (l.product_uom_qty > 0 and l.product_uom_qty = l.qty_cancelled) then 'cancel'
                        when (l.product_uom_qty > 0 and l.product_uom_qty = l.qty_delivered + l.qty_cancelled) then 'sent'
                        else 'in_progress'
                    end as actual_status

        """
        return select_str

    def _from(self):
        from_str = """
                sale_order_line l
                join sale_order s on (l.order_id=s.id)
                left join stock_move sm on (sm.sale_line_id = l.id)
                """
        return from_str

    def _where(self):
        return """
            where sm.state not in ('done', 'draft', 'cancel')
        """

    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                     l.qty_delivered,
                     l.id,
                     l.product_uom,
                     s.state,
                     s.partner_id,
                     s.date_order,
                     s.state,
                     sm.state,
                     sm.date,
                     sm.date_expected
        """
        return group_by_str

    def _select2(self):
        select_str = """
             SELECT
                    min(pl.id) as id,
                    null as sale_line_id,
                    pl.id as sale_order_line_id,
                    pl.product_id as product_id,
                    null as sale_order_id,
                    pl.order_id as purchase_order_id,
                    p.date_order,
                    p.state,
                    sm.state as sm_state,
                    p.partner_id as partner_id,
                    pl.product_qty as product_uom_qty,
                    pl.product_uom,
                    pl.qty_received as qty_delivered,
                    pl.qty_cancelled as qty_cancelled,
                    case
                        when sm.date_expected isnull then sm.date
                        else sm.date_expected
                    end as date_expected,
                    case
                        when (pl.product_qty > 0 and pl.product_qty = pl.qty_cancelled) then 'cancel'
                        when (pl.product_qty > 0 and pl.product_qty = pl.qty_received + pl.qty_cancelled) then 'sent'
                        else 'in_progress'
                    end as actual_status
        """
        return select_str

    def _from2(self):
        from_str = """
                   purchase_order_line pl
                   join purchase_order p on (pl.order_id=p.id)
                   left join stock_move sm on (sm.purchase_line_id = pl.id)
                   """
        return from_str

    def _where2(self):
        return """
            where sm.state not in ('done', 'draft', 'cancel')
        """

    def _group_by2(self):
        group_by_str = """
            GROUP BY pl.product_id,
                     pl.qty_received,
                     pl.id,
                     pl.product_uom,
                     p.state,
                     p.partner_id,
                     p.date_planned,
                     p.date_order,
                     p.state,
                     sm.state,
                     sm.date,
                     sm.date_expected
        """
        return group_by_str

    def _select3(self):
        select_str = """
             SELECT
                    min(id) as id,
                    null as sale_line_id,
                    null as sale_order_line_id,
                    product_id as product_id,
                    null as sale_order_id,
                    null as purchase_order_id,
                    date,
                    'done' as state,
                    state as sm_state,
                    null as partner_id,
                    product_qty as product_uom_qty,
                    product_uom as product_uom ,
                    product_uom_qty as qty_delivered,
                    0 as qty_cancelled,
                    date_expected,
                    case
                        when state = 'cancel' then 'cancel'
                        when state = 'done' then 'sent'
                        else 'in_progress'
                    end as actual_status
        """
        return select_str

    def _from3(self):
        from_str = """
                    stock_move
                   """
        return from_str

    def _where3(self):
        where = """

            where sale_line_id isnull and purchase_line_id isnull and state not in ('draft', 'done', 'cancel')

        """
        return where

    def _group_by3(self):
        group_by_str = """
            GROUP BY product_id,
                     product_uom_qty,
                     id,
                     product_uom,
                     state,
                     partner_id,
                     date,
                     date_expected,
                     state
        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = sale_report
        sql1 = """
                %s
            FROM ( %s )
            %s
            %s
        """ % (
            self._select(),
            self._from(),
            self._where(),
            self._group_by(),
        )
        sql2 = """union
                        %s
                    FROM ( %s )
                    %s
                    %s
                """ % (
            self._select2(),
            self._from2(),
            self._where2(),
            self._group_by2(),
        )
        sql3 = """union
                        %s
                    FROM %s
                    %s
                    %s
                """ % (
            self._select3(),
            self._from3(),
            self._where3(),
            self._group_by3(),
        )

        tools.drop_view_if_exists(self.env.cr, self._table)

        sql = """CREATE or REPLACE VIEW %s as (
           %s
           %s

            order by product_id, date_order) """ % (
            self._table,
            sql1,
            sql2,
        )

        self.env.cr.execute(sql)

    @api.multi
    def _update_status(self):
        for var in self:
            if var.actual_status == "in_progress":
                restante = (
                    var.product_uom_qty - var.qty_delivered - var.qty_cancelled
                )
                if var.qty_available < restante:
                    var.sendable = 0
                else:
                    var.sendable = 1
            else:
                var.sendable = 2
