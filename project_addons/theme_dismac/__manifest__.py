# -*- coding: utf-8 -*-
{
    'name': 'Dismac Theme',
    'version': '1.0',
    'summary': 'Frontend customization for Dismac Website',
    'description': '',
    'category': 'Theme/Ecommerce',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'license': 'AGPL-3',
    'contributors': [
        'Vicente Gutiérrez, <vicente@comunitea.com>',
        'Rubén Seijas <ruben@comunitea.com>',
    ],
    'depends': ['theme_common', 'website_animate', 'breadcrumbs_base_tmp', ],
    'data': [
        'data/theme_dismac_data.xml',
        'views/assets.xml',
    ],
    'images': [
        '/static/description/dismac_description.png',
        '/static/description/dismac_screenshot.png',

    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
}
