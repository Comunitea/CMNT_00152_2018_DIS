# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _

class ChangePasswordWizard(models.TransientModel):
    _inherit = 'change.password.wizard'

    def _default_user_ids(self):
        if self._context.get('active_model') == 'res.partner':
            partner_id = self._context.get('active_model') == 'res.partner' and self._context.get('active_ids') or []
            return [
                (0, 0, {'user_id': user.id, 'user_login': user.login})
                for user in self.env['res.partner'].browse(partner_id).user_ids
            ]
        else:
            return super(ChangePasswordWizard, self)._default_user_ids()

    user_ids = fields.One2many('change.password.user', 'wizard_id', string='Users', default=_default_user_ids)