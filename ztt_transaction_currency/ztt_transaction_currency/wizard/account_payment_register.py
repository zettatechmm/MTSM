# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.depends('currency_id')
    def compute_currency_rate(self):
        for rec in self:
            if rec.company_id.currency_id.id!=rec.currency_id.id:
                rec.currency_rate = rec.currency_id.rate
            else:
                rec.currency_rate = 1

    currency_rate = fields.Float('Currency Rate',default=1,compute='compute_currency_rate',store=True,readonly=False)

    @api.model
    def default_get(self, fields_list):
        # OVERRIDE
        res = super().default_get(fields_list)

        if self._context.get('active_model') == 'account.move':
            lines = self.env['account.move'].browse(self._context.get('active_ids', [])).line_ids
        elif self._context.get('active_model') == 'account.move.line':
            lines = self.env['account.move.line'].browse(self._context.get('active_ids', []))
        else:
            raise UserError(_(
                "The register payment wizard should only be called on account.move or account.move.line records."
            ))
        if lines:
            res['currency_rate'] = lines[0].move_id.currency_rate
            
        return res

    def _get_total_amount_in_wizard_currency_to_full_reconcile(self, batch_result, early_payment_discount=True):
        """ Compute the total amount needed in the currency of the wizard to fully reconcile the batch of journal
        items passed as parameter.

        :param batch_result:    A batch returned by '_get_batches'.
        :return:                An amount in the currency of the wizard.
        """
        self.ensure_one()
        comp_curr = self.company_id.currency_id
        if self.source_currency_id == self.currency_id:
            # Same currency (manage the early payment discount).
            return self._get_total_amount_using_same_currency(batch_result, early_payment_discount=early_payment_discount)
        elif self.source_currency_id != comp_curr and self.currency_id == comp_curr:
            # Foreign currency on source line but the company currency one on the opposite line.
            return self.source_currency_id._convert(
                self.source_amount_currency,
                comp_curr,
                self.company_id,
                self.payment_date,
            ), False
        elif self.source_currency_id == comp_curr and self.currency_id != comp_curr:
            # Company currency on source line but a foreign currency one on the opposite line.
            residual_amount = 0.0
            for aml in batch_result['lines']:
                if not aml.move_id.payment_id and not aml.move_id.statement_line_id:
                    conversion_date = self.payment_date
                else:
                    conversion_date = aml.date
                residual_amount += comp_curr.with_context(currency_rate=1)._convert(
                    aml.amount_residual,
                    self.currency_id.with_context(currency_rate=self.currency_rate),
                    self.company_id,
                    conversion_date,
                )
            return abs(residual_amount), False
        else:
            # Foreign currency on payment different than the one set on the journal entries.
            return comp_curr.with_context(currency_rate=1)._convert(
                self.source_amount,
                self.currency_id.with_context(currency_rate=self.currency_rate),
                self.company_id,
                self.payment_date,
            ), False

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'destination_account_id': self.line_ids[0].account_id.id,
            'write_off_line_vals': [],
            'currency_rate':self.currency_rate,
        }

        if self.payment_difference_handling == 'reconcile':
            if self.early_payment_discount_mode:
                epd_aml_values_list = []
                for aml in batch_result['lines']:
                    if aml.move_id._is_eligible_for_early_payment_discount(self.currency_id, self.payment_date):
                        epd_aml_values_list.append({
                            'aml': aml,
                            'amount_currency': -aml.amount_residual_currency,
                            'balance': aml.currency_id.with_context(currency_rate=aml.move_id.currency_rate)._convert(-aml.amount_residual_currency, aml.company_currency_id.with_context(currency_rate=1), date=self.payment_date),
                        })

                open_amount_currency = self.payment_difference * (-1 if self.payment_type == 'outbound' else 1)
                open_balance = self.currency_id.with_context(currency_rate=self.currency_rate)._convert(open_amount_currency, self.company_id.currency_id.with_context(currency_rate=1), self.company_id, self.payment_date)
                early_payment_values = self.env['account.move']._get_invoice_counterpart_amls_for_early_payment_discount(epd_aml_values_list, open_balance)
                for aml_values_list in early_payment_values.values():
                    payment_vals['write_off_line_vals'] += aml_values_list

            elif not self.currency_id.is_zero(self.payment_difference):
                if self.payment_type == 'inbound':
                    # Receive money.
                    write_off_amount_currency = self.payment_difference
                else: # if self.payment_type == 'outbound':
                    # Send money.
                    write_off_amount_currency = -self.payment_difference

                payment_vals['write_off_line_vals'].append({
                    'name': self.writeoff_label,
                    'account_id': self.writeoff_account_id.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.currency_id.id,
                    'amount_currency': write_off_amount_currency,
                    'balance': self.currency_id.with_context(currency_rate=self.currency_rate)._convert(write_off_amount_currency, self.company_id.currency_id.with_context(currency_rate=1), self.company_id, self.payment_date),
                })
        return payment_vals

    # depends for currency_rate
    @api.depends('can_edit_wizard', 'amount','currency_rate')
    def _compute_payment_difference(self):
        super()._compute_payment_difference()
