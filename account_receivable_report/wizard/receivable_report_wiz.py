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
    from_date = fields.Date(string="From Date", default=date.today().replace(day=1))
    to_date = fields.Date(string="To Date", default=_get_end_of_month)
    tag_ids = fields.Many2many('res.partner.category')
    branch_ids = fields.Many2many('x_branches')
    township_ids = fields.Many2many('res.township')
    state_ids = fields.Many2many('res.country.state')

    excel_file = fields.Binary('Excel File')
    file_name = fields.Char('File Name')

    def get_data(self):
        domain = [('move_type','=','out_invoice'),('amount_residual','>',0)]
        if self.partner_ids.ids:
            domain.append(('partner_id','in',self.partner_ids.ids))
        if self.from_date:
            domain.append(('date', '>=', self.from_date))
        if self.to_date:
            domain.append(('date', '<=', self.to_date))
        if self.tag_ids.ids:
            domain.append(('partner_id.category_id', 'in', self.tag_ids.ids))
        if self.branch_ids.ids:
            domain.append(('partner_id.x_studio_branch', 'in', self.branch_ids.ids))
        if self.township_ids.ids:
            domain.append(('partner_id.township_id', 'in', self.township_ids.ids))
        if self.state_ids.ids:
            domain.append(('partner_id.state_id', 'in', self.state_ids.ids))

        report_data = self.env['account.move'].search(domain, order="date asc")
        return report_data

    def generate_excel_report(self):
        output = io.BytesIO()

        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet("Receivable Report")

        header_style = xlwt.easyxf('font: bold 1, color black; align: horiz left;')
        cell_style = xlwt.easyxf('align: horiz left, vert center, wrap on;')
        number_style = xlwt.easyxf('align: horiz right, vert center, wrap on;')
        date_style = xlwt.easyxf('align: horiz right, vert center,wrap on;',num_format_str='DD/MM/YYYY')
        currency_style = xlwt.easyxf('align: horiz right, vert center;', num_format_str='#,##0')  

        from_date = ['From Date:', self.from_date]
        for col,header in enumerate(from_date):
            if col in [0]:
                sheet.write(0,col,header,header_style)
            elif col in [1]:
                sheet.write(0, col, header, date_style)

        to_date = ['To Date:', self.to_date]
        for col,header in enumerate(to_date):
            if col in [0]:
                sheet.write(1,col,header,header_style)
            elif col in [1]:
                sheet.write(1, col, header, date_style)

        headers = ['Customer Name','Invoice Number','Invoice Date','Due Date','Overdue Days','Invoice Amount','Due Amount','Balance']
        for col,header in enumerate(headers):
            sheet.write(3,col,header,header_style)
            sheet.col(0).width = 8000 
            sheet.col(col + 1).width = 6000 

        report_data = self.get_data()

        row = 4
        for data in report_data:
            due_days = (date.today() - data.invoice_date_due).days
            due_day = due_days if due_days > 0 else 0
            journal = [data.partner_id.name, data.name, data.date, data.invoice_date_due, due_day,data.amount_total, data.amount_residual]

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



        