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
        # Se cambia solo el to_scan para añadir un sorted, pero tengo que heredear toda la función
        """ Find contacts/addresses of the right type(s) by doing a depth-first-search
        through descendants within company boundaries (stop at entities flagged ``is_company``)
        then continuing the search at the ancestors that are within the same company boundaries.
        Defaults to partners of type ``'default'`` when the exact type is not found, or to the
        provided partner itself if no type ``'default'`` is found either. """
        adr_pref = set(adr_pref or [])
        if 'contact' not in adr_pref:
            adr_pref.add('contact')
        result = {}
        visited = set()
        for partner in self:
            current_partner = partner
            while current_partner:
                to_scan = [current_partner]
                # Scan descendants, DFS
                while to_scan:
                    record = to_scan.pop(0)
                    visited.add(record)
                    if record.type in adr_pref and not result.get(record.type):
                        result[record.type] = record.id
                    if len(result) == len(adr_pref):
                        return result
                    to_scan = [c for c in record.child_ids.sorted(
                        key=lambda r: (r.type and -4 or 0) + (r.default_partner_by_type and -2 or 0) + (
                                    r.display_name and -1))
                               if c not in visited
                               if not c.is_company] + to_scan

                # Continue scanning at ancestor if current_partner is not a commercial entity
                if current_partner.is_company or not current_partner.parent_id:
                    break
                current_partner = current_partner.parent_id

        # default to type 'contact' or the partner itself
        default = result.get('contact', self.id or False)
        for adr_type in adr_pref:
            result[adr_type] = result.get(adr_type) or default
        return result
