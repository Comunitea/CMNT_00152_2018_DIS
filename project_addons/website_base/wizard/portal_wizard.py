# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.tools.translate import _
from odoo.tools import email_split
from odoo.exceptions import UserError

from odoo import api, fields, models


_logger = logging.getLogger(__name__)


class PortalWizardUser(models.TransientModel):

    _inherit = 'portal.wizard.user'

    new_passwd = fields.Char(string='New Password', default='')
    login = fields.Char(string='Login', default='')

    @api.multi
    def get_error_messages(self):
        if self._context.get('no_check_email') == True:
            emails = []
            partners_error_empty = self.env['res.partner']
            partners_error_emails = self.env['res.partner']
            partners_error_user = self.env['res.partner']

            for wizard_user in self.with_context(active_test=False).filtered(lambda w: w.in_portal and not w.partner_id.user_ids):
                login = wizard_user.login
                if not login:
                    partners_error_empty |= wizard_user.partner_id
                elif login in emails:
                    partners_error_emails |= wizard_user.partner_id
                user = self.env['res.users'].sudo().with_context(active_test=False).search([('login', '=ilike', login)])
                if user:
                    partners_error_user |= wizard_user.partner_id
                emails.append(login)

            error_msg = []
            if partners_error_empty:
                error_msg.append("%s\n- %s" % (_("Some contacts don't have a valid login: "),
                                    '\n- '.join(partners_error_empty.mapped('display_name'))))
            if partners_error_emails:
                error_msg.append("%s\n- %s" % (_("Several contacts have the same login: "),
                                    '\n- '.join(partners_error_emails.mapped('email'))))
            if partners_error_user:
                error_msg.append("%s\n- %s" % (_("Some contacts have the same login as an existing portal user:"),
                                    '\n- '.join(['%s <%s>' % (p.display_name, p.email) for p in partners_error_user])))
            if error_msg:
                error_msg.append(_("To resolve this error, you can: \n"
                    "- Correct the logins of the relevant contacts\n"
                    "- Grant access only to contacts with unique logins"))
            return error_msg
        else:
            return super(PortalWizardUser, self).get_error_messages()

    @api.multi
    def action_apply(self):
        if self._context.get('no_check_email') == True:
            self.env['res.partner'].check_access_rights('write')
            """ From selected partners, add corresponding users to chosen portal group. It either granted
                existing user, or create new one (and add it to the group).
            """
            error_msg = self.get_error_messages()
            if error_msg:
                raise UserError("\n\n".join(error_msg))

            for wizard_user in self.sudo().with_context(active_test=False):

                group_portal = self.env.ref('base.group_portal')
                #Checking if the partner has a linked user
                user = wizard_user.partner_id.user_ids[0] if wizard_user.partner_id.user_ids else None
                # update partner email, if a new one was introduced
               
                if wizard_user.partner_id.email != wizard_user.email:
                    wizard_user.partner_id.write({'email': wizard_user.email})
                # add portal group to relative user of selected partners
                if wizard_user.in_portal:
                    user_portal = None
                    # create a user if necessary, and make sure it is in the portal group
                    if not user:
                        if wizard_user.partner_id.company_id:
                            company_id = wizard_user.partner_id.company_id.id
                        else:
                            company_id = self.env['res.company']._company_default_get('res.users').id
                        wizard_user.partner_id.portfolio = True
                        wizard_user.partner_id.skip_website_checkout_payment = True
                        user_portal = wizard_user.sudo().with_context(company_id=company_id)._create_user()
                    else:
                        user_portal = user
                    wizard_user.write({'user_id': user_portal.id})
                    if not wizard_user.user_id.active or group_portal not in wizard_user.user_id.groups_id:
                        wizard_user.user_id.write({'active': True, 'groups_id': [(4, group_portal.id)]})
                        # prepare for the signup process
                        wizard_user.user_id.partner_id.signup_prepare()
                    wizard_user.refresh()
                else:
                    # remove the user (if it exists) from the portal group
                    if user and group_portal in user.groups_id:
                        # if user belongs to portal only, deactivate it
                        if len(user.groups_id) <= 1:
                            user.write({'groups_id': [(3, group_portal.id)], 'active': False})
                        else:
                            user.write({'groups_id': [(3, group_portal.id)]})
        else:
            return super(PortalWizardUser, self).action_apply()

    @api.multi
    def _create_user(self):
        if self._context.get('no_check_email') == True:
            company_id = self.env.context.get('company_id')
            user = self.env['res.users'].with_context(no_reset_password=True)._create_user_from_template({
                'email': self.email,
                'login': self.login,
                'partner_id': self.partner_id.id,
                'company_id': company_id,
                'company_ids': [(6, 0, [company_id])],
            })
            
            if self.new_passwd:
                user.update({
                    'password': self.new_passwd
                })
            return user
        else:
            return super(PortalWizardUser, self)._create_user()

    def _default_user_ids(self):
        # for each partner, determine corresponding portal.wizard.user records
        if self._context.get('no_check_email') == True:
            partner_ids = self.env.context.get('active_ids', [])
            contact_ids = set()
            user_changes = []
            for partner in self.env['res.partner'].sudo().browse(partner_ids):
                contact_partners = partner.child_ids | partner
                for contact in contact_partners:
                    # make sure that each contact appears at most once in the list
                    if contact.id not in contact_ids:
                        contact_ids.add(contact.id)
                        in_portal = False
                        login = None
                        if contact.user_ids:
                            in_portal = self.env.ref('base.group_portal') in contact.user_ids[0].groups_id
                            login = contact.user_ids[0].login
                        user_changes.append((0, 0, {
                            'partner_id': contact.id,
                            'email': contact.email,
                            'in_portal': in_portal,
                            'login': login or contact.ref 
                        }))
                return user_changes
            else:
                return super(PortalWizardUser, self)._default_user_ids()

