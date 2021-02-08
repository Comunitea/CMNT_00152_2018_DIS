from odoo import models

class ThemeDismac(models.AbstractModel):
    _inherit = 'theme.utils'

    def _theme_ecommerce_dismac_post_copy(self, mod):
        self.disable_view('website_theme_install.customize_modal')
