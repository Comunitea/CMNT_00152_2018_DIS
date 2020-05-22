# -*- coding: utf-8 -*-

from odoo import models, fields, api,  _
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    def dynamic_category_list(self):
        domain = ['|', ('website_ids', '=', False), ('website_ids', 'in', self.id)]
        return self.env['product.public.category'].sudo().search(domain)

    # DESHABILITAMOS LA REGLA DE ACCESO Y FILTRAMSO DE PORTAL  A PLANTAILLAS AQUI lOS PRODUCTOS
    # EN _get_search_domain se añadirá que si hay precios presonalizado esto se muestren
    # Solo estos en el menu de tarifas y los de la WEB más los dd tarifas (Según permisos)
    @api.multi
    def sale_product_domain(self):
        return [("website_published", "=", True)] + super().sale_product_domain()

    def get_current_pricelist(self):
        """
        :returns: The current pricelist record
        """

        #LA FORZAMOS PARA QUE SOLO MIRE LA DEL PARTNER SI ESTA"HABIITADA Y SI NO LA POR DEFECTO

        # The list of available pricelists for this user.
        # If the user is signed in, and has a pricelist set different than the public user pricelist
        # then this pricelist will always be considered as available
        available_pricelists = self.get_pricelist_available()
        pl = None
        partner = self.env.user.partner_id.commercial_partner_id
        pl = partner.property_product_pricelist

        if available_pricelists and pl not in available_pricelists:
            # If there is at least one pricelist in the available pricelists
            # and the chosen pricelist is not within them
            # it then choose the first available pricelist.
            # This can only happen when the pricelist is the public user pricelist and this pricelist is not in the available pricelist for this localization
            # If the user is signed in, and has a special pricelist (different than the public user pricelist),
            # then this special pricelist is amongs these available pricelists, and therefore it won't fall in this case.
            pl = available_pricelists[0]

        if not pl:
            _logger.error('Fail to find pricelist for partner "%s" (id %s)', partner.name, partner.id)
        #print("PL SELECIONADA %d !!!!! " % pl.id)
        return pl


    @api.multi
    def _prepare_sale_order_values(self, partner, pricelist):
        # Adapta valores de pedido especialmente para los de cartera
        values = super()._prepare_sale_order_values(partner, pricelist)
        if partner.portfolio:
            # Busca el comercial correcto 
            user = partner.user_id
            if not partner.is_company and not user:
                user = partner.commercial_partner_id.user_id

            if  partner.type == 'contact' and partner.parent_id and partner.company_type == 'person':
                # Busca las direcciones de us "padre", sí si es de envñio , devuelve esta 
                # Esto nos permite que funcione bien si el partner es un subcontacto de una "delegacion"
                # o la propia "delegación"
                addr = partner.parent_id.address_get(['delivery'])
                invoice = partner.commercial_partner_id.address_get(['invoice'])['invoice']
                if partner.parent_id.type == 'delivery':
                    delivery = partner.parent_id.id
                else:
                    delivery = addr['delivery']
            elif partner.type == 'delivery' and partner.parent_id:
                addr = partner.commercial_partner_id.address_get(['invoice'])
                delivery = partner.id
                invoice = addr['invoice']
            else:
                
                addr = partner.address_get(['delivery', 'invoice'])
                invoice = addr['invoice']
                delivery = addr['delivery']

            values.update({
                'partner_invoice_id': invoice,
                'partner_shipping_id': delivery,
                'user_id': user.id,
             })
            
        if partner.skip_website_checkout_payment:
            sale_type = self.env['sale.order.type'].sudo().search([('telesale', '=', True)])
        else:
            sale_type = self.env['sale.order.type'].sudo().search([('web', '=', True)])
        if sale_type:
            values ['type_id'] = sale_type[0].id
        return values

    @api.multi
    def get_new_cart(self):
        partner = self.env.user.partner_id
        pricelist_id = request.session.get('website_sale_current_pl') or self.get_current_pricelist().id
        if not self._context.get('pricelist'):
            self = self.with_context(pricelist=pricelist_id)

        pricelist = self.env['product.pricelist'].browse(pricelist_id).sudo()
        so_data = self._prepare_sale_order_values(partner, pricelist)
        sale_order = self.env['sale.order'].with_context(force_company=request.website.company_id.id).sudo().create(so_data)

        if sale_order:
            request.session['sale_order_id'] = sale_order.id
            request.session['sale_last_order_id'] = sale_order.id
            sale_order.partner_id.write({'last_website_so_id': sale_order.id})
            return sale_order
        else:
            request.session['sale_order_id'] = None
            request.session['sale_last_order_id'] = None
            request.session['website_sale_current_pl'] = None
            partner.write({'last_website_so_id': None})
            return self.env['sale.order']

    @api.multi
    def _compute_checkout_skip_payment(self):
        for rec in self:
            sale_order = self.env['sale.order'].sudo().browse(request.session['sale_order_id'])
            if sale_order and sale_order.need_validation:
                if request.session.uid:
                    rec.checkout_skip_payment =\
                        request.env.user.partner_id.skip_website_checkout_payment or sale_order.need_validation
            else:
                super()._compute_checkout_skip_payment()


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    dynamic_cat_menu = fields.Boolean(string='Dynamic categories menu', default=False)
