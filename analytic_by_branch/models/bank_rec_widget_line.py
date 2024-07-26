# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models, Command

class BankRecWidgetLine(models.Model):
    _inherit = "bank.rec.widget.line"
    
    @api.depends('source_aml_id', 'account_id', 'partner_id')
    def _compute_analytic_distribution(self):
        super()._compute_analytic_distribution()
        for line in self:
            if line.flag in ('liquidity', 'aml'):
                line.analytic_distribution = line.source_aml_id.analytic_distribution
            elif line.flag in ('tax_line', 'early_payment'):
                line.analytic_distribution = line.analytic_distribution
            else:
                model_distribution = self.env['account.analytic.distribution.model']._get_distribution({
                    "partner_id": line.partner_id.id,
                    "partner_category_id": line.partner_id.category_id.ids,
                    "account_prefix": line.account_id.code,
                    "company_id": line.company_id.id,
                    "branch_id": line.source_aml_id.move_id.x_studio_branch.id
                    })
                line.analytic_distribution = model_distribution or line.analytic_distribution