# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductPublicCategory(models.Model):
    _inherit = "res.users"

    quotes_ids = fields.One2many('sale.quote', 'user_id', string='Request quotes',
                                 help=_("Request quotes that contains this category"))


class ProductOffer(models.Model):
    _name = "sale.quote"
    _description = _("Request Quote")
    _order = "date desc, id desc"
    _rec_name = 'name'

    active = fields.Boolean(default=True)
    name = fields.Char(string=_('Subject'), index=True)
    date = fields.Datetime(string='Sent on', index=True)
    website_id = fields.Many2one('website', string=_("Website"), ondelete='cascade')
    user_id = fields.Many2one('res.users', string=_('User'), ondelete='cascade')
    contact_phone = fields.Char(string="Contact phone", size=9, readonly=False,
                                states={'current': [('readonly', False)]})
    contact_email = fields.Char(string="Contact email", size=50, readonly=False,
                                states={'current': [('readonly', False)]})
    state = fields.Selection(selection=[('current', 'Current'),('sent', 'Sent')],
                             string=_('State'), default='current', readonly=False, )
    observations = fields.Html(_("Observations"), strip_style=True)
    metadata = fields.Html(_("Metadata"), strip_style=True)
    products_found = fields.Html(_("Products found in website"), strip_style=True)
    products_not_found = fields.Html(_("Products not found in website"), strip_style=True)
    product_ids = fields.Many2many('product.template', 'product_quote_rel', 'product_id', 'quote_id',
                                   string=_('Products'))

    @api.multi
    def get_current_quote(self):
        user = self.env.user
        Quote = self.env['sale.quote']
        domain = [('user_id', '=', user.id), ('website_id', '=', self.env['website'].get_current_website().id)]
        return Quote.search(domain + [('state', '=', 'current')], limit=1)
