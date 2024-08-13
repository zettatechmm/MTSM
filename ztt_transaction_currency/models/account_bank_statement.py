from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv.expression import get_unaccent_wrapper

from odoo.addons.base.models.res_bank import sanitize_account_number

from xmlrpc.client import MAXINT


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    currency_rate = fields.Float('Currency Rate',default=1, store=True,readonly=False)

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    currency_rate = fields.Float('Currency Rate', default=0, store=True, readonly=False)
    
    @api.model_create_multi
    def create(self, vals_list):
        st_line = super().create(vals_list)
        st_line.move_id.write({'currency_rate': st_line.currency_rate})
        return st_line
    
    @api.onchange('amount', 'date', 'company_id')
    def _onchange_amount(self):
        if not self.amount:               
            self.currency_rate = 0
            self.statement_id.currency_rate = 0
        elif self.date and self.currency_id != self.env.company.currency_id and not self.currency_rate:            
            currency_rate= self.env['res.currency']._get_conversion_rate(
                    from_currency=self.currency_id,
                    to_currency=self.env.company.currency_id,
                    company=self.company_id, 
                    date=self.date,
                )
            self.currency_rate = currency_rate
            self.statement_id.currency_id = currency_rate

    def _prepare_move_line_default_vals(self, counterpart_account_id=None):
        """ Prepare the dictionary to create the default account.move.lines for the current account.bank.statement.line
        record.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        """
        self.ensure_one()

        if not counterpart_account_id:
            counterpart_account_id = self.journal_id.suspense_account_id.id

        if not counterpart_account_id:
            raise UserError(_(
                "You can't create a new statement line without a suspense account set on the %s journal.",
                self.journal_id.display_name,
            ))

        company_currency = self.journal_id.company_id.sudo().currency_id
        journal_currency = self.journal_id.currency_id or company_currency
        foreign_currency = self.foreign_currency_id or journal_currency or company_currency

        journal_amount = self.amount
        if foreign_currency == journal_currency:
            transaction_amount = journal_amount
        else:
            transaction_amount = self.amount_currency
        if journal_currency == company_currency:
            company_amount = journal_amount
        elif foreign_currency == company_currency:
            company_amount = transaction_amount
        else:
            company_amount = journal_currency.with_context(currency_rate=self.currency_rate)\
                ._convert(journal_amount, company_currency.with_context(currency_rate=company_currency.rate), self.journal_id.company_id, self.date)
                
        liquidity_line_vals = {
            'name': self.payment_ref,
            'move_id': self.move_id.id,
            'partner_id': self.partner_id.id,
            'account_id': self.journal_id.default_account_id.id,
            'currency_id': journal_currency.id,
            'amount_currency': journal_amount,
            'debit': company_amount > 0 and company_amount or 0.0,
            'credit': company_amount < 0 and -company_amount or 0.0,           
        }

        # Create the counterpart line values.
        counterpart_line_vals = {
            'name': self.payment_ref,
            'account_id': counterpart_account_id,
            'move_id': self.move_id.id,
            'partner_id': self.partner_id.id,
            'currency_id': foreign_currency.id,
            'amount_currency': -transaction_amount,
            'debit': -company_amount if company_amount < 0.0 else 0.0,
            'credit': company_amount if company_amount > 0.0 else 0.0,
        }
        return [liquidity_line_vals, counterpart_line_vals]