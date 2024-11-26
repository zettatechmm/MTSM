import io
import xlwt
import base64
import calendar
from odoo import models, fields, _
from odoo.exceptions import UserError
from datetime import date


class PartnerSelect(models.TransientModel):
    _name = 'wizard.receivable.report'
    _description = "Wizard Receivable Report"

    def _get_end_of_month(self):
        today = date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]
        return date(today.year, today.month, last_day)
    
    partner_ids = fields.Many2many('res.partner')
    print_date = fields.Date(string="Print Date", default=date.today())
    tag_ids = fields.Many2many('res.partner.category')
    branch_ids = fields.Many2many('x_branches')
    township_ids = fields.Many2many('res.township')
    state_ids = fields.Many2many('res.country.state')

    excel_file = fields.Binary('Excel File')
    file_name = fields.Char('File Name')

    def get_data(self):
        
        query = """
                    SELECT partner_name,invoice_name,date,invoice_date_due,overdue_days,amount_currency,amount_total,amount_residual,partner_id,currency_id FROM (
                SELECT rp.name AS partner_name, move.name AS invoice_name, aml.date,
                move.invoice_date_due AS invoice_date_due,
                CASE WHEN (%(print_date)s - move.invoice_date_due::date) > 0 THEN (%(print_date)s - move.invoice_date_due::date) ELSE 0 END AS overdue_days,
                (SUM(aml.amount_currency)
                - COALESCE(SUM(part_debit.debit_amount_currency), 0)
                + COALESCE(SUM(part_credit.credit_amount_currency), 0)
                ) AS amount_currency,
                SUM(aml.balance) AS amount_total,
                (SUM(aml.balance)
                - COALESCE(SUM(part_debit.amount), 0)
                + COALESCE(SUM(part_credit.amount), 0)
                ) AS amount_residual,
                aml.partner_id AS partner_id,
                aml.currency_id AS currency_id
                FROM account_move_line aml
                JOIN account_journal journal ON journal.id = aml.journal_id
                JOIN account_account account ON account.id = aml.account_id
                JOIN account_move move ON move.id = aml.move_id
                JOIN res_partner rp ON rp.id = aml.partner_id
                LEFT JOIN res_township township ON township.id = rp.township_id
                LEFT JOIN res_partner_res_partner_category_rel rel ON rel.partner_id = rp.id
                LEFT JOIN res_partner_category category ON category.id = rel.category_id
                LEFT JOIN res_country_state state ON state.id = rp.state_id
                LEFT JOIN x_branches branch ON branch.id = rp.x_studio_branch
                JOIN res_currency currency ON move.currency_id = currency.id
                LEFT JOIN LATERAL (
                    SELECT
                        SUM(part.amount) AS amount,
                        SUM(part.debit_amount_currency) AS debit_amount_currency,
                        part.debit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <=  %(print_date)s AND part.debit_move_id = aml.id
                    GROUP BY part.debit_move_id
                ) part_debit ON TRUE
                LEFT JOIN LATERAL (
                    SELECT
                        SUM(part.amount) AS amount,
                        SUM(part.credit_amount_currency) AS credit_amount_currency,
                        part.credit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <=  %(print_date)s AND part.credit_move_id = aml.id
                    GROUP BY part.credit_move_id
                ) part_credit ON TRUE
                WHERE account.account_type='asset_receivable'
                AND move.state='posted'
                AND aml.date <=  %(print_date)s
                AND move.move_type = 'out_invoice'
                AND rp.id IN %(partner_ids)s
                AND township.id IN %(township_ids)s
                AND category.id IN %(tag_ids)s
                AND state.id IN %(state_ids)s
                AND branch.id IN %(branch_ids)s
                GROUP BY rp.name,aml.partner_id,account.code,aml.date,move.name,move.invoice_date_due,aml.currency_id
            ) receivable
            WHERE receivable.amount_residual > 0
            ORDER BY partner_id,date
"""
        
        township_ids =  self.township_ids.ids if self.township_ids else self.env['res.township'].search([]).ids
        partner_ids =  self.partner_ids.ids if self.partner_ids else self.env['res.partner'].search([]).ids
        tag_ids =  self.tag_ids.ids if self.tag_ids else self.env['res.partner.category'].search([]).ids
        state_ids = self.state_ids.ids if self.state_ids else self.env['res.country.state'].search([]).ids
        branch_ids = self.branch_ids.ids if self.branch_ids else self.env['x_branches'].search([]).ids

         
        params = {'print_date': self.print_date,
                  'partner_ids': tuple(partner_ids),
                  'tag_ids':  tuple(tag_ids),
                  'branch_ids':  tuple(branch_ids),
                  'township_ids': tuple(township_ids),
                  'state_ids': tuple(state_ids)}
        
        self.env.cr.execute(query, params)
        res = self.env.cr.dictfetchall()
        return res

    def generate_excel_report(self):
        output = io.BytesIO()

        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet("Receivable Report")

        header_style = xlwt.easyxf('font: bold 1, color black; align: horiz left;')
        cell_style = xlwt.easyxf('align: horiz left, vert center, wrap on;')
        number_style = xlwt.easyxf('align: horiz right, vert center, wrap on;')
        date_style = xlwt.easyxf('align: horiz right, vert center,wrap on;',num_format_str='DD/MM/YYYY')
        currency_style = xlwt.easyxf('align: horiz right, vert center;', num_format_str='#,##0')  

        print_date = ['As Of', self.print_date]
        for col,header in enumerate(print_date):
            if col in [0]:
                sheet.write(0,col,header,header_style)
            elif col in [1]:
                sheet.write(0, col, header, date_style)


        headers = ['Customer Name','Invoice Number','Invoice Date','Due Date','Overdue Days','Invoice Amount','Due Amount','Balance']
        for col,header in enumerate(headers):
            sheet.write(3,col,header,header_style)
            sheet.col(0).width = 8000 
            sheet.col(col + 1).width = 6000 
 
        report_data = self.get_data()

        row = 4
        for data in report_data:
            journal = [data['partner_name'], data['invoice_name'], data['date'], data['invoice_date_due'], data['overdue_days'],data['amount_total'], data['amount_residual']]

            for col, value in enumerate(journal):
                if col in [2,3]:
                    sheet.write(row, col, value, date_style)
                elif col in [4]:
                    sheet.write(row, col, value, number_style)
                elif col in [5,6]:
                    sheet.write(row, col, value, currency_style)
                else:
                    sheet.write(row, col, value, cell_style)

            if row == 4:
                # First row: Balance = Due Amount
                sheet.write(row, 7, xlwt.Formula(f"G{row + 1}"),currency_style)
            else:
                # Subsequent rows: Balance = Previous Balance + Current Due Amount
                sheet.write(row, 7, xlwt.Formula(f"H{row} + G{row + 1}"),currency_style)


            sheet.row(row).height_mismatch = True
            sheet.row(row).height = 256 * 2
            row += 1
            
        workbook.save(output)
        output.seek(0)
        self.excel_file = base64.b64encode(output.getvalue())
        self.file_name = "receivable_report.xls"

        return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self._name}/{self.id}/excel_file/{self.file_name}?download=true',
                'close': True, 
            }



        