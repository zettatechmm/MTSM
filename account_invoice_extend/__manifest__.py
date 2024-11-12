# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Accounting Invoice Inherit',
    'summary': 'Add Columns in Customer Invoices',
    'category': 'Accounting/Invoice',
    'description': """
Accounting Invoice
==================
    """,
    'depends': ['base', 'account', 'contacts','partner_extend',],
    'data': [
        'views/custom_invoice.xml',
        'views/account_move_view.xml',
    ],
    'auto_install': True,
    'installable': True,
    'license': "LGPL-3",
}
