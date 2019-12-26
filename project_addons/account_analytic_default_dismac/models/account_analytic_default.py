from odoo import fields, models, api


class AccountAnalyticDefault(models.Model):
    _inherit = "account.analytic.default"
    categ_id = fields.Many2one(
        'product.category', string='Categoría',
        ondelete='cascade',
        help="Select the category corresponding to an analytic account "
             "which will be used on the lines of invoices or account moves"
    )

    @api.model
    def account_get(self, product_id=None, partner_id=None, user_id=None,
                    date=None, company_id=None):
        if product_id:
            categ_id = self.env['product.product'].browse(
                product_id).categ_id.id
        else:
            categ_id = None
        domain = []
        if product_id:
            domain += ['|', ('product_id', '=', product_id)]
        domain += [('product_id', '=', False)]
        if categ_id:
            domain += ['|', ('categ_id', '=', categ_id)]
        domain += [('categ_id', '=', False)]
        if partner_id:
            domain += ['|', ('partner_id', '=', partner_id)]
        domain += [('partner_id', '=', False)]
        if company_id:
            domain += ['|', ('company_id', '=', company_id)]
        domain += [('company_id', '=', False)]
        if user_id:
            domain += ['|', ('user_id', '=', user_id)]
        domain += [('user_id', '=', False)]
        if date:
            domain += ['|', ('date_start', '<=', date),
                       ('date_start', '=', False)]
            domain += ['|', ('date_stop', '>=', date),
                       ('date_stop', '=', False)]
        best_index = -1
        res = self.env['account.analytic.default']
        for rec in self.search(domain):
            index = 0
            if rec.product_id: index += 1
            if rec.categ_id: index += 1
            if rec.partner_id: index += 1
            if rec.company_id: index += 1
            if rec.user_id: index += 1
            if rec.date_start: index += 1
            if rec.date_stop: index += 1
            if index > best_index:
                res = rec
                best_index = index
        return res
