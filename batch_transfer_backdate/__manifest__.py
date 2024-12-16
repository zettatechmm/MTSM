# -*- coding: utf-8 -*-
{
    'name': "Batch Transfer Backdate",
    'summary': """ """,
    'description': """""",
    'author': "Zettatech",
    'website': "",
    'category': 'Extra',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'stock_picking_batch'],
    # always loaded
    'data': [
        "security/picking_batch_backdate_group.xml",   
        "security/ir.model.access.csv",   
        "wizard/picking_batch_backdate.xml",
        "data/picking_batch_backdate_data.xml",
        ],
    'license': 'LGPL-3',

}
