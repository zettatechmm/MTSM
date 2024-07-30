# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models, Command

class BankRecWidgetLine(models.Model):
    _inherit = "bank.rec.widget.line"
    
    @api.depends('source_aml_id', 'account_id', 'partner_id')
    def _compute_analytic_distribution(self):
        super()._compute_analytic_distribution()
        analytic_distribution = False
        for line in self:
            if line.flag in ('liquidity', 'aml'):
                analytic_distribution = line.source_aml_id.analytic_distribution
                line.analytic_distribution = line.source_aml_id.analytic_distribution
            elif line.flag in ('tax_line', 'early_payment'):
                line.analytic_distribution = line.analytic_distribution
            else:
                model_distribution = analytic_distribution
                line.analytic_distribution = model_distribution or line.analytic_distribution