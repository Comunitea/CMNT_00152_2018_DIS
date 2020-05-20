# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time

from odoo import http, _, fields
from odoo.http import request

from odoo.addons.website.controllers.main import Website


class Website(Website):

    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        response = super(Website, self).web_login(redirect=redirect, *args, **kw)
        if not redirect and request.params['login_success'] and not (request.env['res.users'].browse(request.uid).has_group('base.group_user')):
            return http.redirect_with_hash('/shop')
        return response