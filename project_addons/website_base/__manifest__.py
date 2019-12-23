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
        'seo_base',
        # 'website_blog_base',
        # 'follow_us_base',
        # 'multi_company_base',
        # 'mass_mailing',
        # 'website_form_builder',
        # 'website_sale_product_brand',
        'payment_redsys',
        # 'website_sale_hide_price',
    ],
    'data': [
        'templates/account.xml',
        'templates/forms.xml',
        'templates/header.xml',
        'templates/simulated_products.xml',
        'templates/offer.xml',
        'templates/product.xml',
        'templates/quote.xml',
        'views/product_views.xml',
        'views/quote_views.xml',
        'security/ir.model.access.csv',
    ],
    'images': [
        '/static/description/icon.png',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
}
