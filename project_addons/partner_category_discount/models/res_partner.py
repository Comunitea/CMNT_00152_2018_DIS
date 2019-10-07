# -*- coding: utf-8 -*-
# © 2019 Comunitea - Santi Argüeso <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    category_discount_ids = fields.One2many('category.discount', 'partner_id')
