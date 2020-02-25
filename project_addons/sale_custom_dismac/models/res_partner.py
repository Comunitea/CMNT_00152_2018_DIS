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


    def address_get(self, adr_pref=None):
        # Se cambia para ajustar a solicitud del cliente
        
        adr_pref = set(adr_pref or [])
        if 'contact' not in adr_pref:
            adr_pref.add('contact')
        result = {}
        for partner in self:

            for adr in adr_pref:
                if partner.type == adr:
                    result[adr] = partner.id
                else:
                    default = partner.commercial_partner_id.child_ids.sorted(
                        lambda r: r.default_partner_by_type).filtered(
                        lambda p: p.type == adr and p.default_partner_by_type)
                    if len(default) == 1:
                        result[adr] = default.id
                    else:
                        if default and default[0].default_partner_by_type:
                            result[adr] = default[0].id
                        else:
                            result[adr] = partner.commercial_partner_id.id

        # default to type 'contact' or the partner itself
        default = result.get('contact', self.id or False)
        for adr_type in adr_pref:
            result[adr_type] = result.get(adr_type) or default
        return result
