# -*- coding: utf-8 -*-


from odoo import fields,http
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website_sale.controllers.main import QueryURL
from odoo.addons.website_sale.controllers import main
from odoo.addons.website.controllers.main import Website
from odoo.addons.web_editor.controllers.main import Web_Editor
import math
import os
import base64
import uuid
from lxml import etree, html

main.PPG = 18
PPG=main.PPG
import logging
_logger = logging.getLogger(__name__)


class Web_Editor(Web_Editor):

    @http.route("/web_editor/save_scss", type="json", auth="user", website=True)
    def save_scss(self, url, bundle_xmlid, content):
        IrAttachment = request.env["ir.attachment"]

        if url != '/dismac_ecommerce/static/src/scss/options/colors/color_picker.scss':
            return super(Web_Editor, self).save_scss(url,bundle_xmlid,content)



        # Check if the file to save had already been modified

        datas = base64.b64encode((content or "\n").encode("utf-8"))
        custom_url = '/dismac_ecommerce/static/src/scss/options/colors/color_picker'+str(request.website.id)+'.scss'


        custom_attachment = self.get_custom_attachment(custom_url)

        if custom_attachment:
            # If it was already modified, simply override the corresponding attachment content
            custom_attachment.write({"datas": datas})
        else:
            # If not, create a new attachment to copy the original scss file content, with its modifications
            new_attach = {
                'name': custom_url,
                'type': "binary",
                'mimetype': "text/scss",
                'datas': datas,
                'datas_fname': url.split("/")[-1],
                'url': custom_url,
            }
            new_attach.update(self.save_scss_attachment_hook())
            IrAttachment.create(new_attach)

            # Create a view to extend the template which adds the original file to link the new modified version instead
            IrUiView = request.env["ir.ui.view"]

            def views_linking_url(view):
                """
                Returns whether the view arch has some html link tag linked to the url.

                (note: searching for the URL string is not enough as it could appear in a comment or an xpath expression.)
                """
                return bool(etree.XML(view.arch).xpath("//link[@href='{}']".format(url)))

            view_to_xpath = IrUiView.get_related_views(bundle_xmlid, bundles=True).filtered(views_linking_url)

            new_view = {
                'name': custom_url,
                'key': 'web_editor.scss_%s' % str(uuid.uuid4())[:6],
                'mode': "extension",
                'inherit_id': view_to_xpath.id,
                'arch': """
                    <data inherit_id="%(inherit_xml_id)s" name="%(name)s">
                        <xpath expr="//link[@href='%(url_to_replace)s']" position="attributes">
                            <attribute name="href">%(new_url)s</attribute>
                        </xpath>
                    </data>
                """ % {
                    'inherit_xml_id': view_to_xpath.xml_id,
                    'name': custom_url,
                    'url_to_replace': url,
                    'new_url': custom_url,
                }
            }
            new_view.update(self.save_scss_view_hook())
            IrUiView.create(new_view)

        request.env["ir.qweb"].clear_caches()

class Website(Website):

    @http.route('/update_scss_file', type='json', auth='public', website=True)
    def update_file(self, **kw):
        context = dict(request.context)
        if kw['write_str']:
            module_str = '/'.join((os.path.realpath(__file__)).split('/')[:-2])
            file_url = module_str + '/static/src/scss/options/colors/website_'+str(request.website.id)+'_color_picker.scss'
            f = open(module_str + '/static/src/scss/options/colors/website_'+str(request.website.id)+'_color_picker.scss', 'w+')
            f.write(kw['write_str'])
            f.close();
            _logger.info("Color scss updated")
        return request.env["ir.qweb"]._get_asset('website.assets_frontend',options=context,css=True)

    @http.route()
    def theme_customize(self, enable, disable, get_bundle=True):
        """ enable or Disable lists of ``xml_id`` of the inherit templates """
        def set_active(ids, active):
            if ids:
                real_ids = self.get_view_ids(ids)
                request.env['ir.ui.view'].browse(real_ids).write({'active': active})

        set_active(disable, False)
        set_active(enable, True)
        template = ''
        context = dict(request.context)
        if enable:
            for i in enable:
                if i.startswith('dismac_ecommerce.header_layout_'):
                     if  not i.endswith('_css'):
                         templ = i+'_css'
                         views = request.env['ir.ui.view'].search([('key','ilike','dismac_ecommerce.header_layout_')])
                         for v in views:
                            if v.key.endswith('_css'):
                                set_active([v.key], False)
                         set_active([templ], True)

                if i.startswith('dismac_ecommerce.footer_layout_'):
                     if  not i.endswith('_css'):
                         templ = i+'_css'
                         views = request.env['ir.ui.view'].search([('key','ilike','dismac_ecommerce.footer_layout_')])
                         for v in views:
                            if v.key.endswith('_css'):
                                set_active([v.key], False)
                         set_active([templ], True)

        if get_bundle:
            context = dict(request.context)
            return request.env["ir.qweb"]._get_asset('web.assets_frontend', options=context)

        return True


class WebsiteSale(WebsiteSale):


    @http.route(['/variant_change_images'], auth="public", website=True)
    def variant_change_images(self, product):
        if product:
            data =  http.request.env['product.product'].sudo().search([('id','=',product)])
        if data:
            return http.request.render('dismac_ecommerce.image_box_product', {
                    'variant': data,
                    'product': data.product_tmpl_id,
                    'website': request.website,
            })

    @http.route(
        ['/page/product_brands'],
        type='http',
        auth='public',
        website=True)
    def product_brands(self, **post):
        cr, context, pool = (request.cr,
                             request.context,
                             request.registry)
        b_obj = request.env['product.brand']
        domain = []
        if post.get('search'):
            domain += [('name', 'ilike', post.get('search'))]
        brand_ids = b_obj.search(domain)

        keep = QueryURL('/page/product_brands', brand_id=[])
        values = {'brand_rec': brand_ids,
                  'keep': keep}
        if post.get('search'):
            values.update({'search': post.get('search')})
        return request.render(
            'dismac_ecommerce.product_brands',
            values)

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        website = request.website
        quantities_per_page = None
        quantities_per_page = request.env[
            'product.qty_per_page'].search([], order='sequence')
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = quantities_per_page[
                    0].name if quantities_per_page else PPG
            res = super(WebsiteSale, self).shop(page, category, search, ppg, **post)
            if 'ppg' in post:
                post["ppg"] = ppg
        else:
            ppg = quantities_per_page[0].name if quantities_per_page else PPG
            res = super(WebsiteSale, self).shop(page, category, search, ppg, **post)

        res.qcontext.update({
            'ppg': ppg,
            'quantities_per_page': quantities_per_page
        })

        if post.get('brand') or post.get('product_collection'):
            attrib_list = request.httprequest.args.getlist('attrib')
            attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
            attributes_ids = {v[0] for v in attrib_values}
            attrib_set = {v[1] for v in attrib_values}

            domain = self._get_search_domain(search, category, attrib_values)

            if post.get('brand'):
                product_designer_obj = request.env['product.brand']
                brand_ids = product_designer_obj.search([('id', '=', int(post.get('brand')))])
                if brand_ids:
                    domain += [('product_brand_id', 'in', brand_ids.ids)]

            if post.get('product_collection'):
                prod_collection_rec = request.env['multitab.configure'].search([('id','=',int(post.get('product_collection')))])
                if prod_collection_rec:
                    prod_id_list = list({each_p.product_id.id for each_p in prod_collection_rec.product_ids})
                    domain += [('id','in',prod_id_list)]
            keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))

            pricelist_context = dict(request.env.context)

            if not pricelist_context.get('pricelist'):
                pricelist = request.website.get_current_pricelist()
                pricelist_context['pricelist'] = pricelist.id
            else:
                pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

            request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

            url = "/shop"
            if search:
                post["search"] = search
            if category:
                category = request.env['product.public.category'].browse(int(category))
                url = "/shop/category/%s" % slug(category)
            if attrib_list:
                post['attrib'] = attrib_list

            categs = request.env['product.public.category'].search([('parent_id', '=', False)])
            Product = request.env['product.template']

            parent_category_ids = []
            if category:
                parent_category_ids = [category.id]
                current_category = category
                while current_category.parent_id:
                    parent_category_ids.append(current_category.parent_id.id)
                    current_category = current_category.parent_id

            product_count = Product.search_count(domain)

            pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
            products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

            ProductAttribute = request.env['product.attribute']

            if products:
                selected_products = Product.search(domain, limit=False)
                attributes = ProductAttribute.search([('attribute_line_ids.product_tmpl_id', 'in', selected_products.ids)])
            else:
                attributes = ProductAttribute.browse(attributes_ids)

            from_currency = request.env.user.company_id.currency_id
            to_currency = pricelist.currency_id
            compute_currency, pricelist_context, pricelist = self._get_compute_currency_and_context()
            res.qcontext.update({
                'search': search,
                'category': category,
                'attrib_values': attrib_values,
                'attrib_set': attrib_set,
                'pager': pager,
                'products': products,
                'search_count': product_count,
                'bins': TableCompute().process(products, ppg),
                'categories': categs,
                'attributes': attributes,
                'compute_currency': compute_currency,
                'keep': keep,
                'parent_category_ids': parent_category_ids,
                'product_collection': post.get('product_collection'),
            })
        return res


    @http.route()
    def product(self, product, category='', search='', **kwargs):
        res = super(WebsiteSale, self).product(product, category, search, **kwargs)
        res.qcontext.update({'page': kwargs.get('page'), 'ppg': kwargs.get('ppg')})
        return res

    @http.route(['/shop/cart/clean_cart'], type='json', auth="public", website=True)
    def clean_cart(self, type_id=None):
        order = request.website.sale_get_order()
        request.website.sale_reset()
        if order:
            order.sudo().unlink();
        return {}

    @http.route(['/shop/product/update_cart_popup'], type='http', auth="public", website=True)
    def update_cart_popup(self):
        order = request.website.sale_get_order()
        return request.render("dismac_ecommerce.product_cart", {'website':request.website})

    @http.route(['/shop/product/whishlists/move_to_cart'], type='json', auth="public", website=True)
    def move_to_cart(self, line_id=None):
        if line_id:
            product_data=request.env['product.wishlist'].browse(line_id)
            request.website.sale_get_order(force_create=1)._cart_update(product_id=int(product_data.product_id.id), add_qty=float(1), set_qty=float(1))
        return True

    @http.route(['/shop/product/whishlists/add_all_to_cart'], type='json', auth="public", website=True)
    def add_all_to_cart(self, line_id=None):
        cr,uid=request.cr,request.uid
        line_ids=request.env['product.wishlist'].search([('user_id','=',uid)])
        for data in line_ids:
            request.website.sale_get_order(force_create=1)._cart_update(product_id=int(data.product_id.id), add_qty=float(1), set_qty=float(1))
        return True



    @http.route('/update_my_wishlist', type="http", auth="public", website=True)
    def qv_update_my_wishlist(self, **kw):
        if kw['prod_id']:
            self.add_to_wishlist(product_id=int(kw['prod_id']))
        return

    @http.route('/get_qv_prod_variant', type="json", auth="public", website=True)
    def get_qv_product_variant(self, **kw):
        ret = {}
        attribute_values_array = kw['attribute_values_array']
        prod_template = http.request.env['product.template'].search([("id",'=',int(kw['prod_template_id']))])
        if prod_template and len(prod_template) == 1:
            data = []
            for each_variant in prod_template[0].product_variant_ids:
                db_attribute_values_array = []
                for each_attrb_value in each_variant.attribute_value_ids:
                    num_of_values = http.request.env['product.attribute.value'].search([('attribute_id','=',each_attrb_value.attribute_id.id)])
                    if num_of_values and len(num_of_values) > 1:
                        db_attribute_values_array.append(each_attrb_value.id)
                if (len(set(db_attribute_values_array).intersection(set(attribute_values_array))) == len(attribute_values_array)) and (len(db_attribute_values_array) == len(attribute_values_array)):
                    data.append(each_variant)
            if len(data) == 1:
                ret['product_product_id'] = data[0].id
        return ret


    @http.route()
    def cart(self, access_token=None, revive='', **post):
        res = super(WebsiteSale, self).cart(access_token, revive, **post)
        if post.get('type') == 'cart_lines_popup':
            return request.render('dismac_ecommerce.cart_lines_popup_content', res.qcontext)
        else:
            return res

    @http.route('/check_magnifier_status', type='json', auth='public', website=True)
    def check_magnifier_status(self, **kw):
        # status = False
        view_rec = request.env['ir.ui.view'].search([('key','=like','dismac_ecommerce.product_picture_magnify')]) #('id','=',1307),('key','=like','dismac_ecommerce.product_picture_magnify')
        return {'status': view_rec.active if view_rec else False}


