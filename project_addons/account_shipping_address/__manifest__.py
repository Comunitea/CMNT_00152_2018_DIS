# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Account shipping address',
    'summary': 'Add the shipping address on invoices and account moves',
    'version': '11.0.1.0.0',
    'category': 'Account',
    'website': 'comunitea.com',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'sale'
    ],
    'data': [
        'views/account.xml'
    ],
}
