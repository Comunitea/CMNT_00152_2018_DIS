# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api, _

class Pricelist(models.Model):
    
    _inherit = "product.pricelist"

    date_start = fields.Date('Start Date', help="Starting date for the pricelist item validation")
    date_end = fields.Date('End Date', help="Ending valid for the pricelist item validation")

class ProductPricelistItem(models.Model):

    _inherit = "product.pricelist.item"