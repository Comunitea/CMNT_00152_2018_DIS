# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class WebsiteOffer(models.Model):
    _name = "report.website.offer"
    _description = "Website Offers"
    _auto = False
    _order = 'id desc'

    model_id = fields.Char('Model ID', readonly=True)
    odoo_model = fields.Char('Odoo Model', readonly=True)
    name = fields.Char('Offer Name', readonly=True)
    description_short = fields.Char('Short description', readonly=True)
    description_full = fields.Char('Full description', readonly=True)
    website_id = fields.Many2one('website', 'Website ID', readonly=True)
    product_public_category_id = fields.Many2one('product.public.category', 'Product Category', readonly=True)
    website_published = fields.Boolean('Is published', readonly=True)
    start_date = fields.Date(string='Start Date', readonly=True)
    end_date = fields.Date(string='End Date', readonly=True)

    def _query(self, with_clause='', fields={}, orderby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            ROW_NUMBER () OVER (ORDER BY model_id) as id, 
            model_id, 
            name, 
            odoo_model,
            website_id, 
            product_public_category_id,
            description_short,
            description_full,
            website_published,
            start_date,
            end_date
        """

        for field in fields.values():
            select_ += field

        from_ = """
                (
                    select po.id as model_id, 
                    po.name as name, 
                    po.description_short as description_short, 
                    po.description_full as description_full, 
                    po.website_id as website_id,
                    po.category_id as product_public_category_id,
                    'product.offer' AS odoo_model,
                    po.website_published as website_published,
                    po.start_date as start_date,
                    po.end_date as end_date
                    from product_offer po 
                    JOIN product_public_category ppc ON po.category_id = ppc.id
                    where po.start_date <= NOW() and (po.end_date >= NOW() or po.end_date is NULL)
                    AND ppc.website_published = True
                    AND (ppc.parent_id IS NULL OR ppc.parent_id IN (SELECT id from product_public_category WHERE website_published = True))

                    UNION

                    select pt.id as model_id, 
                    pt.name as name, 
                    pt.website_description_short as description_short, 
                    pt.website_description as description_full, 
                    pt.website_id as website_id,
                    ppcpt.product_public_category_id as product_public_category_id,
                    'product.template' AS odoo_model,
                    pt.is_published AS website_published,
                    NULL as start_date,
                    NULL as end_date
                    from product_template pt
                    LEFT JOIN product_public_category_product_template_rel ppcpt ON pt.id = ppcpt.product_template_id
                    LEFT JOIN product_style_product_template_rel pspt ON pt.id = pspt.product_template_id
                    LEFT JOIN product_style ps ON  pspt.product_style_id = ps.id
                    WHERE ps.html_class = 'oe_ribbon_promo'
                    and pt.active = True
                ) x 
        """

        return '%s (SELECT %s FROM %s)' % (with_, select_, from_)

    @api.model_cr
    def init(self):
        # self._table = report_website_offer
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
