# -*- coding: utf-8 -*-

import unicodedata
import re
import random
from odoo import api, fields, models, tools, _


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    offer_ids = fields.One2many('product.offer', 'category_id', string='Product Offers',
                                help=_("Offers that contains this category"))

    def get_parent_categories(self, category):
        new_category = self.search([('id', '=', int(category))])
        parent_category_ids = [new_category.id]
        current_category = new_category
        while current_category.parent_id:
            parent_category_ids.append(current_category.parent_id.id)
            current_category = current_category.parent_id
        return parent_category_ids


class ProductOffer(models.Model):
    _name = "product.offer"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Oferta"
    _order = "website_sequence, name"
    _rec_name = 'name'

    def _default_website(self):
        return self.env['website'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)

    website_id = fields.Many2one('website', string=_("Website"), default=_default_website, ondelete='cascade')
    active = fields.Boolean(default=True)
    name = fields.Char(_('Title'), index=True, required=True, translate=True)
    description_short = fields.Char(_('Subtitle'), index=True, translate=True,
                           help=_("Short description to be show under title like a paragraph in plain text"))
    description_full = fields.Html(_("Full HTML Description"), strip_style=True, required=True, translate=True)
    description_sale = fields.Text(
        'Sale Description', translate=True,
        help="A description of the Offer that you want to communicate to your customers. "
             "Only in case of products, this description will be copied to every Sales Order, "
             "Delivery Order and Customer Invoice/Credit Note")
    sequence = fields.Integer(_('Internal Sequence'), default=1,
                              help=_('Gives the sequence order when displaying a offer list'))
    website_sequence = fields.Integer(_('Website Sequence'), default=lambda self: self._default_website_sequence(),
                                      help=_("Determine the display order in the Website"))
    category_id = fields.Many2one('product.public.category', string='Related Category')
    offer_image_ids = fields.One2many('product.offer.image', 'offer_id', string='Images')
    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary(_("Image"), attachment=True, help=_("This field holds the image used as image for the "
                                                              "offer, limited to 1024x1024px."))
    image_medium = fields.Binary(_("Medium-sized image"), attachment=True,
                                 help=_("Medium-sized image of the offer. It is automatically resized as a 128x128px "
                                        "image, with aspect ratio preserved, only when the image exceeds one of "
                                        "those sizes. Use this field in form views or some kanban views."))
    image_small = fields.Binary(_("Small-sized image"), attachment=True,
                                help=_("Small-sized image of the offer. It is automatically "
                                       "resized as a 64x64px image, with aspect ratio preserved. "
                                       "Use this field anywhere a small image is required."))
    website_published = fields.Boolean(string=_('Published'), default=True,
                                       help=_("Only published offers are visible on the website"))
    website_meta_title = fields.Char(string=_("Meta Title"), translate=True)
    website_meta_description = fields.Text(string=_("Meta Description"), translate=True)
    website_meta_keywords = fields.Char(string=_("Meta Keywords"), translate=True)
    slug = fields.Char(_("Friendly URL"))
    attachment_id = fields.Binary(string=_("Attachment"), attachment=True)
    attachment_filename = fields.Char(string=_("Attachment Filename"))
    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.context_today)
    end_date = fields.Date(string='End Date')
    # TODO: Include them in xml offer views to set by settings
    website_size_x = fields.Integer('Size X', default=1)
    website_size_y = fields.Integer('Size Y', default=1)
    website_style_ids = fields.Many2many('product.style', string='Styles')

    @api.multi
    def get_attachment_id(self):
        self.ensure_one()
        domain = [('res_model', '=', self._name), ('res_field', '=', 'attachment_id'), ('res_id', '=', self.id), ]
        return self.env['ir.attachment'].sudo().search(domain)

    def _default_website_sequence(self):
        self._cr.execute("SELECT MIN(website_sequence) FROM %s" % self._table)
        min_sequence = self._cr.fetchone()[0]
        return min_sequence and min_sequence - 1 or 10

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        slug = vals.get('slug', self.slug)
        if not slug:
            slug = vals.get('name', False) or self.name
        vals.update({'slug': self._slug_validation(slug)})
        super(ProductOffer, self).write(vals)
        vals.pop('slug')
        return True

    @api.model
    def create(self, vals):
        slug = vals.get('slug', False)
        if not slug or slug == '':
            slug = vals['name']
        vals.update({'slug': self._slug_validation(slug)})
        return super(ProductOffer, self).create(vals)

    def _slug_validation(self, value):
        # Unicode validation and apply max length
        uni = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub('[\W_]', ' ', uni).strip().lower()
        value = re.sub('[-\s]+', '-', value)
        value = value[:60]
        # Check if this SLUG value already exists in any offer
        it_exists = self.sudo().search([('slug', '=', value)], limit=1).id
        if it_exists and not it_exists == self.id:
            # Add random URL part
            value = '%s-%d' % (value, random.randint(0, 999))
        return value

    def _get_combination_info(self):
        return False


class ProductOfferImage(models.Model):
    _name = 'product.offer.image'
    _description = _("Product Offer Image")
    _rec_name = 'name'

    name = fields.Char(_('Name'), translate=True)
    image = fields.Binary(_('Image'), attachment=True)
    offer_id = fields.Many2one('product.offer', 'Related Offer', copy=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    historical_ordered_qty = fields.Integer(compute="_get_product_historical_ordered_qty")
    partner_last_order = fields.Datetime(compute="_get_partner_last_order")

    @api.multi
    def _get_product_historical_ordered_qty(self):
        for template in self:

            context = self._context
            current_uid = context.get('uid')
            partner_id = self.env['res.users'].browse(current_uid).partner_id._get_domain_partner()

            if context.get('selected_partner'):
                partner_id = self.env['res.users'].browse(context.get('selected_partner'))
            
            customer_domain = [('partner_id', 'child_of', partner_id.id), ('state', '=', 'sale'), ('product_tmpl_id', '=', template.id)]
            
            customer_product_data = self.env['sale.report'].sudo().read_group(customer_domain, ['product_uom_qty'], ['product_tmpl_id', 'partner_id'])

            template.historical_ordered_qty = customer_product_data[0]['product_uom_qty']

    @api.multi
    def _get_partner_last_order(self):

        for template in self:

            context = self._context
            current_uid = context.get('uid')
            partner_id = self.env['res.users'].browse(current_uid).partner_id._get_domain_partner()

            if context.get('selected_partner'):
                partner_id = self.env['res.users'].browse(context.get('selected_partner'))
            
            customer_domain = [('partner_id', 'child_of', partner_id.id), ('state', '=', 'sale'), ('product_tmpl_id', '=', template.id)]
            
            customer_product_data = self.env['sale.report'].sudo().search_read(customer_domain, ['confirmation_date'], order="confirmation_date desc")

            template.partner_last_order = customer_product_data[0]['confirmation_date']

    @api.multi
    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
    
        self.ensure_one()

        combination_info = super(ProductTemplate, self.with_context(round=False))._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        tax_price = round(combination_info['price'] * (1 + self.sudo().taxes_id[0].amount / 100), 2)
        context = self._context
        current_uid = context.get('uid')
        partner = self.env['res.users'].browse(current_uid).partner_id
        if partner.portfolio:
            decimals = self.env['res.users'].browse(current_uid).partner_id.decimals
        else:
            decimals = 2
        combination_info.update(
            tax_price=tax_price,
            decimals=decimals
        )
    
        return combination_info