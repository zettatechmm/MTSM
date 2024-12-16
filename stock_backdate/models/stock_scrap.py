# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from datetime import date


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    date_done = fields.Datetime(
        'Date', readonly=False, default=fields.Datetime.now, required=True)

    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(
        related="company_id.remark_for_scrap", string="Is Remarks")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_for_scrap", string="Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('date_done')
    def onchange_date_done(self):
        if str(self.date_done.date()) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def do_scrap(self):
        self._check_company()
        for scrap in self:
            scrap.name = self.env['ir.sequence'].next_by_code(
                'stock.scrap') or _('New')
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            # master: replace context by cancel_backorder
            move.with_context(is_scrap=True)._action_done()
            scrap.write({'state': 'done'})
            # scrap.date_done = fields.Datetime.now()
            if scrap.should_replenish:
                scrap.do_replenish()
        return True
