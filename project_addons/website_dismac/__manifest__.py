# -*- coding: utf-8 -*-
{
    'name': 'Website Dismac',
    'version': '1.0',
    'summary': 'Customization for Dismac website.',
    'description': '',
    'category': 'Website',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'license': 'AGPL-3',
    'contributors': [
        'Rubén Seijas <ruben@comunitea.com>',
        'Vicente Gutiérrez, <vicente@comunitea.com>',
    ],
    'depends': [
        'website_base',
    ],
    'data': [
        'data/website_data.xml',
        'data/menu_data.xml',
        'data/default_data.xml',
        'templates/forms.xml',
        'templates/cookies.xml',
        'templates/account.xml',
        'templates/footer.xml',
        'templates/header.xml',
    ],
    'images': [
        '/static/description/icon.png',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
}
