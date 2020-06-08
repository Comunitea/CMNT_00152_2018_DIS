# Copyright 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    print ("MIGRACIÓN!!!!!!. INICIA CAMBIO DE PRECIO")
    env['product.product']._set_last_purchase_fixed()
    print ("FINALIZA CAMBIO DE PRECIO")
