# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime


class PickngBackdateWizard(models.TransientModel):
    _name = 'sh.picking.backdate.wizard'
    _description = "Picking Backdate Wizard"

    stock_picking_ids = fields.Many2many('stock.picking',)
    scheduled_date = fields.Datetime(
        string="Scheduled Date", required=True, default=datetime.now())
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(
        related="company_id.remark_for_picking", string="Is Remarks")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_for_picking", string="Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('scheduled_date')
    def onchange_scheduled_date(self):
        if str(self.scheduled_date.date()) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def open_picking_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')

        return{
                'name': 'Assign Backdate',
                'res_model': 'sh.picking.backdate.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('stock_backdate.stock_picking_backdate_wizard_view_form').id,
                'context': {
                    'default_stock_picking_ids': [(6, 0, active_ids)],
                },
                'target': 'new',
                'type': 'ir.actions.act_window'
            }

    def assign_backdate(self):
        for stock_picking in self.stock_picking_ids:
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

            stock_picking.write({'scheduled_date': self.scheduled_date,
                                'remarks': self.remarks if self.remarks else ''})
            stock_picking.write({'date_done': self.scheduled_date})