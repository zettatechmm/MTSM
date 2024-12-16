# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    scrap_id = fields.Many2one('stock.scrap', string="scrap id")

    remarks_for_picking = fields.Text(
        string="Remarks for picking", related="picking_id.remarks")
    is_remarks_for_picking = fields.Boolean(
        related="company_id.remark_for_picking", string="Is Remarks for picking")

    remarks_for_scrap = fields.Text(string="Remarks for scrap")
    is_remarks_for_scrap = fields.Boolean(
        related="company_id.remark_for_scrap", string="Is Remarks for scrap")

    def write(self, vals):
        for rec in self:
            if rec.company_id.backdate_for_picking:
                if rec.picking_id:
                    vals['date'] = rec.picking_id.scheduled_date

            if rec.company_id.backdate_for_scrap:
                if rec.scrap_id:
                    vals['date'] = rec.scrap_id.date_done
                    vals['remarks_for_scrap'] = rec.scrap_id.remarks

        return super().write(vals)
