# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Accounting Reports Inherit',
    'summary': 'View and create reports',
    'category': 'Accounting/Accounting',
    "author": "Zettatech",
    'description': """
Accounting Reports
==================
    """,
    'depends': ['account_reports'],
    'data': [
        # 'data/pdf_export_templates.xml',
        'report/receivable_report.xml',
        'report/report_actions.xml',
        'report/menu_items.xml',
    ],
    'auto_install': False,
    'installable': True,
    # 'assets': {       
    #     'web.report_assets_common': [
    #         # 'account_reports/static/src/scss/account_pdf_export_template.scss',
    #     ],

    #     'web.assets_backend': [
    #         'account_reports_extend/static/src/components/**/*',
    #         # 'account_reports/static/src/js/**/*',
    #         # 'account_reports/static/src/widgets/**/*',
    #     ],

    # },
    'license': "LGPL-3",
}
