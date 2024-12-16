# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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

    def write(self, vals):
        for rec in self:
            if 'date_done' in vals:
                vals['date_done'] = rec.scheduled_date

            return super().write(vals)

    def _set_scheduled_date(self):
        for picking in self:
            # if picking.state in ('done', 'cancel'):
            #     raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
            picking.move_ids.write({'date': picking.scheduled_date})
