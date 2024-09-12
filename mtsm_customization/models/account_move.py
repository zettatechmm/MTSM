from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError

class AccountBankStatementLine(models.Model): 
    _inherit = "account.move"
        
    x_studio_branch = fields.Many2one("x_branches", string="Branch", default=lambda self: self.env.user.x_studio_default_branch.id)
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        compute='_compute_journal_id', inverse='_inverse_journal_id', store=True, readonly=False, precompute=True,
        required=True,
        check_company=True,
        domain="[('id', 'in', suitable_journal_ids), '|', ('x_studio_branch', '=', False), ('x_studio_branch', '=', x_studio_branch)]",
    )

    consignment_no = fields.Char(string="Consignment No", copy=False)
    
    def _get_journal(self, branch_id):
        res = self.env['account.journal'].search([('type' , '=', 'sale'), ('company_id', '=', self.env.company.id), ('x_studio_branch', '=', branch_id)], limit=1)
        return res
    
    @api.onchange('x_studio_branch')
    def _onchange_branch(self):
        if self.x_studio_branch and self.move_type == 'out_invoice':       
            self.journal_id = self._get_journal(self.x_studio_branch.id).id
    
    def _search_default_journal(self):
        if self.payment_id and self.payment_id.journal_id:
            return self.payment_id.journal_id
        if self.statement_line_id and self.statement_line_id.journal_id:
            return self.statement_line_id.journal_id
        if self.statement_line_ids.statement_id.journal_id:
            return self.statement_line_ids.statement_id.journal_id[:1]

        journal_types = self._get_valid_journal_types()
        company = self.company_id or self.env.company
        domain = [
            *self.env['account.journal']._check_company_domain(company),
            ('type', 'in', journal_types), '|', ('x_studio_branch' , '=', False), ('x_studio_branch', '=', self.env.user.x_studio_default_branch.id)
        ]

        journal = None
        # the currency is not a hard dependence, it triggers via manual add_to_compute
        # avoid computing the currency before all it's dependences are set (like the journal...)
        if self.env.cache.contains(self, self._fields['currency_id']):
            currency_id = self.currency_id.id or self._context.get('default_currency_id')
            if currency_id and currency_id != company.currency_id.id:
                currency_domain = domain + [('currency_id', '=', currency_id)]
                journal = self.env['account.journal'].search(currency_domain, limit=1)

        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)

        if not journal:
            error_msg = _(
                "No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
                company_name=company.display_name,
                journal_types=', '.join(journal_types),
            )
            raise UserError(error_msg)

        return journal
