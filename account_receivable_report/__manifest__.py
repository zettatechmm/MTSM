# -*- coding: utf-8 -*-
{
    'name': "Account Receivable Report(Detail)",

    'summary': """
             Account Report by wizard""",

    'description': """
                Account Report(Detail)
                """,

    'author': "Zettatech",
    'website': "",
    'category': 'Accounting',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account_reports','sale'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/receivable_report_wiz.xml',
        'views/menu.xml'
    ],
    # only loaded in demonstration mode
    'license': 'LGPL-3',
}
