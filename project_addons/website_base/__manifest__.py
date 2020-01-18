# -*- coding: utf-8 -*-
{
    'name': 'MultiWebsite Base Module',
    'version': '1.0',
    'summary': 'Backend customization for all companies and their websites.',
    'description': '',
    'category': 'Website',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'license': 'AGPL-3',
    'contributors': [
        'Rubén Seijas <ruben@comunitea.com>',
    ],
    'depends': [
        'ecommerce_base',
        #'website_seo_settings',
        'breadcrumbs_base_tmp',
    ],
    'data': [
        'templates/head.xml',
        'templates/account.xml',
        'templates/forms.xml',
        'templates/header.xml',
        'templates/simulated_products.xml',
        'templates/offer.xml',
        'templates/product.xml',
        'templates/quote.xml',
        'templates/portal_history.xml',
        'views/product_views.xml',
        'views/quote_views.xml',
        'security/ir.model.access.csv',
        'security/sale_security.xml'
    ],
    'images': [
        '/static/description/icon.png',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
}
