from odoo import api, Command, fields, models, _

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"


    branch_id = fields.Many2one("x_branches", string="Branch")
    
    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id:
            self.branch_id = self.partner_id.x_studio_branch.id

    def _prepare_move_line_default_vals(self, counterpart_account_id=None):
        res  = super()._prepare_move_line_default_vals(counterpart_account_id)
        if res and res[0] and res[1]:
            self.move_id.x_studio_branch = self.branch_id.id
            distribution = self.env['account.analytic.distribution.model']._get_distribution({
                        "partner_id": self.partner_id.id,
                        "partner_category_id": self.partner_id.category_id.ids,
                        "company_id": self.company_id.id,
                        "branch_id": self.branch_id.id
                        })
            analytic_distribution = distribution or False
            res[0].update({'analytic_distribution':analytic_distribution})
            res[1].update({'analytic_distribution':analytic_distribution})
        return res