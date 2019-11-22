# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
PROCUREMENT_PRIORITIES = [('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'), ('3', 'Very Urgent')]

class ResPartner(models.Model):

    _inherit = "res.partner"

    whole_orders = fields.Boolean("Shipping Whole orders")
    no_valued_picking = fields.Boolean("No valued picking")
    require_num_order = fields.Boolean("Requires num order")
    zone_id = fields.Many2one("partner.zone", "Zone")
    route_id = fields.Many2one("delivery.route", "Delivery Route")
    priority = fields.Selection(PROCUREMENT_PRIORITIES, 'Priority', default='1')