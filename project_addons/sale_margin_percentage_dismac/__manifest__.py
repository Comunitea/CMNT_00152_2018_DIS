# © 2014 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Percentage of margins in Sales Orders For Dismac   ',
    'version': '12.0.0.0.0',
    'category': 'Sales Management',
    'description': """
    """,
    'author': 'Comunitea',
    'depends': ['sale',
                'stock_account_custom'],
    'data': ["views/sale_view.xml",
             "data/ir_cron.xml"],
}
