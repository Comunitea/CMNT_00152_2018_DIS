# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self):
        '''
            No viene la fecha en contexto, solo en el active_domain,
            por lo que necesitamos volver a ponerla en contexto
        '''
        import ipdb; ipdb.set_trace()
        if self._context.get('active_domain'):
            for domain in self._context['active_domain']:
                if domain[0] == 'invoice_until':
                    self = self.with_context(invoice_until=domain[2])
        return super().create_invoices()
