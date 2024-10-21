# -*- coding: utf-8 -*-
{
    'name': "Stock Ledger Report(Detail)",

    'summary': """
             Stock Ledger Report By Location""",

    'description': """
                Stock Ledger Report(Detail)
                """,

    'author': "Zettatech",
    'website': "",
    'category': 'Inventory',
    'version': '0.2',
    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'license': 'LGPL-3',
}
