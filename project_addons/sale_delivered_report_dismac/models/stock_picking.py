# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, api
from datetime import datetime, timedelta


class StockPicking(models.Model):

    _inherit ="stock.picking"

    @api.one
    def _set_scheduled_date(self):
        # import ipdb; ipdb.set_trace()
        ## Si se cambia el valor de la fecha planificada del albarán, debe cambairse la fecha prevista, ya que el calculod el acantidad
        ## no tiene en cuenta la fecha prevista de los albaranes de entrada si no la fecha original
        vals = {'date_expected': self.scheduled_date,
                'date': self.scheduled_date}
        self.move_lines.filtered(lambda x: x.state != 'done').write(vals)
