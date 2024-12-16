# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime


class PickngBackdateWizard(models.TransientModel):
    _name = 'picking.batch.backdate.wizard'
    _description = "Batch Transfer Backdate Wizard"

    picking_batch_ids = fields.Many2many('stock.picking.batch',)
    scheduled_date = fields.Datetime(
        string="Scheduled Date", required=True, default=datetime.now())  

    def open_picking_batch_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')
        return{
                'name': 'Assign Backdate',
                'res_model': 'picking.batch.backdate.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('batch_transfer_backdate.picking_batch_backdate_wizard_view_form').id,
                'context': {
                    'default_picking_batch_ids': [(6, 0, active_ids)],
                },
                'target': 'new',
                'type': 'ir.actions.act_window'
            }

    def assign_backdate(self):
        for stock_picking in self.picking_batch_ids.picking_ids:
            stock_moves = self.env['stock.move'].search(
                [('picking_id', '=', stock_picking.id)])                
            product_moves = self.env['stock.move.line'].search( 
                [('move_id', 'in', stock_moves.ids)])
            account_moves = self.env['account.move'].search([('stock_move_id', 'in', stock_moves.ids)])
            valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id', 'in', stock_moves.ids)])
            for account_move in account_moves:
                account_move.button_draft()
                account_move.name = '/'
                account_move.sudo().date = self.scheduled_date
                account_move.action_post()
            for layer in valuation_layers:
                self.env.cr.execute("""
                    Update stock_valuation_layer set create_date='%s' where id=%s; 
                """ %(self.scheduled_date, layer.id))
            for move in stock_moves:
                move.write({'date': self.scheduled_date})
            for move in product_moves:
                move.date = self.scheduled_date

            stock_picking.sudo().scheduled_date = self.scheduled_date
            stock_picking.sudo().date_done = self.scheduled_date
        self.picking_batch_ids.sudo().write({'scheduled_date': self.scheduled_date})
            