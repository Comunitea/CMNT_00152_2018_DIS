# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class CreditControlCommunication(models.Model):
    _inherit = "credit.control.communication"


    @api.multi
    @api.returns('mail.mail')
    def _generate_emails(self):
        """ We replace the original function to add the body_html """
        emails = self.env['mail.mail']
        required_fields = [
            'subject',
            'body_html',
            'email_from',
            'email_to',
        ]
        for comm in self:
            template = comm.current_policy_level.email_template_id
            email_values = template.generate_email(comm.id)
            email_values['message_type'] = 'email'
            # added check
            if not email_values.get('body_html'):
                email_values['body_html'] = comm.current_policy_level.custom_mail_text

            email_values.pop('model', None)
            email_values.pop('res_id', None)
            attachment_list = email_values.pop('attachments', [])
            email = emails.create(email_values)

            state = 'sent'
            if not all(email_values.get(field) for field in required_fields):
                state = 'email_error'
            comm.credit_control_line_ids.write({
                'mail_message_id': email.id,
                'state': state,
            })
            email.attachment_ids = [(0, 0, {
                'name': att[0],
                'datas': att[1],
                'datas_fname': att[0],
                'res_model': 'mail.mail',
                'res_id': email.id,
                'type': 'binary',
            }) for att in attachment_list]
            emails |= email
        return emails