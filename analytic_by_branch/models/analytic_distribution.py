# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountAnalyticDistributionModel(models.Model):
    _inherit = 'account.analytic.distribution.model'

    branch_id = fields.Many2one('x_branches',string='Branch',ondelete='cascade',
        help="Select a branch which will use analytic account specified in analytic default (e.g. create new customer invoice or Sales order if we select this product, it will automatically take this as an analytic account)",
    )

    def _create_domain(self, fname, value):
        return super()._create_domain(fname, value)
