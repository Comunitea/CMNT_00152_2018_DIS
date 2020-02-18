# © 2020 Comunitea
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models, api
import base64
import logging



class AccountInvoiceIntegration(models.Model):
    _inherit = 'account.invoice.integration'

    @api.multi
    def send_by_mail(self):
        """ Generates a new mail.mail. Template is rendered on record given by
        res_id and model coming from template.

        :param int res_id: id of the record to render the template
        :param bool force_send: send email immediately; otherwise use the mail
            queue (recommended);
        :param dict email_values: update generated mail with those values to further
            customize the mail;
        :param str notif_layout: optional notification layout to encapsulate the
            generated email;
        :returns: id of the mail.mail that was created """
        self.ensure_one()
        Mail = self.env['mail.mail']
        Template = self.env["mail.template"]
       
        # create a mail_mail based on values, without attachments
        mail_template = Template.search([("name", "=", "Envio factura Xunta")])
        values = mail_template.generate_email(self.id)
        ##values['attachment_ids'] = False
        values['recipient_ids'] = [(4, pid) for pid in values.get('partner_ids', list())]
        
        # add a protection against void email_from
        if 'email_from' in values and not values.get('email_from'):
            values.pop('email_from')
       
        mail = Mail.create(values)

        mail.write({'attachment_ids': [(6, 0, [self.attachment_id.id,])]})

        mail.send()
        return mail.id
