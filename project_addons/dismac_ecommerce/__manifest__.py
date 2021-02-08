# -*- coding: utf-8 -*-

{
    'name': 'Ecommerce Dismac Theme',
    'category': 'Theme/Ecommerce',
    'sequence': 5,
    'summary': 'Ecommerce Dismac Theme',
    'version': '12.0.0.8.0',
    'description': '',
    'author': 'Comunitea',
    'website' : 'https://www.comunitea.com',
    'license': 'AGPL-3',
    'contributors': [
        'Manuel Alejandro Núñez Liz <alejandro@zeleiro.com>',
    ],
    'depends': [
    'account',
        'account',
        'partner_statement',
        'web',
        'website',
        'website_base',
        'website_canonical_url',
        'website_form',
        'website_logo',
        'website_menu_by_user_status',
        'website_sale',
        'website_theme_install'
    ],
    'data': [
		# data
		# views
		'views/custom_shop.xml',
        'views/website_setting.xml',
        'views/website_menu.xml',
        'views/options.xml',
        'views/multi_tab_configure.xml',
        'views/product_brand.xml',
        'views/product_category.xml',
        # 'views/product_tabs.xml',
        'views/snippet_embeded.xml',
        
        
        # security
        'security/ir.model.access.csv',
        # Templates
        'templates/assets.xml',
        'templates/breadcrumb.xml',
        'templates/header_footer.xml',
        'templates/mega_menu.xml',
        'templates/product_brand_page.xml',
        'templates/product_brand.xml',
        'templates/product_slider_snippet.xml',
        'templates/product_slider.xml',
        'templates/snippet_multitab_slider.xml',
        'templates/snippets.xml',
        'templates/templates.xml',
        'templates/wishlist.xml',
        
        
    ],
    'demo': '',
    'images': [
        '/static/description/icon.png',
        '/static/description/dismac_description.png',
        '/static/description/dismac_screenshot.png',

    ],
    'installable': True,
    'application': True,
}
