# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def remig_act_qties(self, force=False):
        print ("Revisando {}".format(self.mapped('name')))
        for so in self:
            print ("Pedido {}".format(so.name))
            pick = so.picking_ids.filtered(lambda x: ('ALB/' in x.name or'WH/OUT/' in x.name) and x.state == 'cancel')
            alb_p = so.picking_ids.filtered(lambda x: 'ALB_P/' in x.name and any(not move.sale_line_id for move in x.move_lines))

            if pick and alb_p:

                for sol in so.order_line:
                    print ('-    > Linea {}'.format(sol.display_name))
                    product_id = sol.product_id
                    pick_move = pick.move_lines.filtered(lambda x: x.sale_line_id and x.state == 'cancel' and x.product_id == product_id)

                    if pick_move:
                        print('-    -    > PICK MOVE {}: {}'.format(pick_move.display_name, product_id.display_name))
                        alb_p_id = pick_move.id + 1
                        out_move = alb_p.move_lines.filtered(lambda x: x.product_id == product_id and not x.sale_line_id )

                        if out_move:
                            print('-    -    > OUT MOVE {}: {}'.format(out_move.display_name, product_id.display_name))
                            if out_move.id != alb_p_id and not force:
                                print ("\n -------------- Revisar el albaran {} -------------------".format(alb_p.name))
                            else:
                                print ('LINK ....')
                                out_move.sale_line_id = pick_move.sale_line_id


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def check_sale_lines(self):
        return all(x.sale_line_id for x in self.move_lines)

    @api.multi
    def remig_act_qties(self):
        for pick in self.filtered(lambda x: 'ALB_P/' in x.name):
            pick.sale_id.remig_act_qties()

    @api.multi
    def mig_picks_with_moves_with_out_sale_lines(self):

        for pick in self.filtered(lambda x: 'ALB_P/' in x.name):

            if all(smp.sale_line_id for smp in pick.move_lines):
                continue
            sale_id = pick.sale_id
            if not sale_id:
                continue
            product_ids = pick.move_lines.mapped('product_id')
            print ('Revisando {}'.format(pick.name))
            for product in product_ids:
                smp = pick.move_lines.filtered(lambda x: x.product_id == product)
                solp = sale_id.order_line.filtered(lambda x: x.product_id == product)
                if len(smp) == 1 and len(solp) == 1 and not smp.sale_line_id:
                    msg= "Actualizado el movimiento {}: {} \n con la línea {}".format(pick.name, smp.display_name, solp.display_name)
                    print (msg)
                    msg = "Actualizado el movimiento {}: {} <br/> con la línea {}".format(pick.name, smp.display_name,
                                                                                       solp.display_name)
                    pick.message_post(body=msg)

                    smp.sale_line_id = solp





    @api.multi
    def picks_confirmed_to_done(self):
        pick_to_transfer = self.env['stock.picking']
        spt = self.env['stock.picking.type']
        spt_src_id = spt.search([('barcode', '=', 'WH-PICK')])
        pick_domain = [('picking_type_id', '=', spt_src_id.id), ('state', '!=', 'done')]
        for pick in self.env['stock.picking'].search(pick_domain):
            dest_pick_ids = pick.move_lines.mapped('move_dest_ids').mapped('picking_id')
            if pick.backorder_id and len(dest_pick_ids.filtered(lambda x: x.state != 'done')) == 1:

                ## BACK ORDER CON UNA LINEA
                ## LO TENFO QUE MIGRAR A VERSION NUEVA Y CANCELAR EL DESTINO
                ## NO TRANSFERIRLO
                print('\n-------Backorder en {}\n'.format(pick.name))
                continue

            if len(dest_pick_ids) > 1:
                print ('\n-------Error en {}\n'.format(pick.name))
                continue
            #for dest_pick in dest_pick_ids:
            #    print ("{}: Estado {} >>>> {} en estado {}".format(pick.name, pick.state, dest_pick.name, dest_pick.state))
            if dest_pick_ids and len(dest_pick_ids) == 1 and dest_pick_ids.state in ('done', 'cancel'):
                pick_to_transfer |= pick
                print ("Transfiero {}".format(pick.name))
                #pick.action_done()

        #print("Transfiero {}".format(pick_to_transfer.mapped('name')))


    def do_migration(self, dest_pick):
        def mig_name(old_name):
            new_name = old_name.replace('WH/PICK', 'ALB_P')
            new_name = new_name.replace('PICK', 'ALB_P')
            return new_name
        pick = self
        pick.name = mig_name(pick.name)

        location_dest_id = dest_pick.move_lines.mapped('location_dest_id')
        dest_pick.action_cancel()
        pick.picking_type_id = dest_pick.picking_type_id
        pick.location_dest_id = dest_pick.location_dest_id
        pick.move_lines.write({'location_dest_id': location_dest_id.id})
        pick.move_line_ids.write({'location_dest_id': location_dest_id.id})
        for line in pick.move_lines:
            line.name = line.product_id.display_name

    @api.multi
    def migration_to_1_step(self):

        done_ids=error_ids=pick_to_mig = pick_to_cancel = sp = self.env['stock.picking']
        spt = self.env['stock.picking.type']

        spt_src_id = spt.search([('barcode', '=', 'WH-PICK')])
        spt_src_id.ensure_one()
        spt_dest_id = spt.search([('barcode', '=', 'WH-DELIVERY')])
        print (spt_dest_id)
        spt_dest_id.ensure_one()

        pick_domain = [('batch_id', '=', False), ('id', 'in', self.ids), ('picking_type_id', '=', spt_src_id.id), ('state', 'not in', ('cancel', 'done'))]
        pick_ids = sp.search(pick_domain)
        total = len(pick_ids)
        print ("Revisando {} albaranes".format(total))
        for pick in pick_ids:
            total -= 1
            print("Alabran {} Faltan{}".format(pick.name, total))
            dest_pick_ids = pick.move_lines.mapped('move_dest_ids').mapped('picking_id').filtered(lambda x: x.state!='done')
            pick_dest_ids_orig_ids = dest_pick_ids.mapped('move_lines').mapped('move_orig_ids').filtered(lambda x: x.state!='done').mapped('picking_id')
            if len(dest_pick_ids)==1 and len(pick_dest_ids_orig_ids)==1:
                try:
                    pick.do_migration(dest_pick_ids)
                    done_ids |= pick
                except:
                    error_ids |= pick

            if pick.backorder_id and len(dest_pick_ids.filtered(lambda x: x.state != 'done')) == 1:

                pick_to_cancel |= dest_pick_ids.filtered(lambda x: x.state != 'done')
                pick_to_mig |= pick
                continue

            pick_dest_ids_orig_ids = dest_pick_ids.mapped('move_lines').mapped('move_orig_ids').mapped('picking_id')

        print ("REALIZADOS: {} \n ERROR: {}".format(done_ids.ids, error_ids.ids))
        ## 1º unlink los moves
        ## 2ª cancel cliente
        ## 3º cambiar nombre, tipo y ubicación de destino en los albaranes origen y movimientos de destino
        ## 4º si estan en una agrupación se mantienen

