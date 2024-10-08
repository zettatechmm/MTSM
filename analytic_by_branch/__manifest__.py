# -*- coding: utf-8 -*-

{
    "name" : "Analytic By Branch",
    "version" : "17.0.0.0",
    "category" : "Analytic By Branch",
    "depends" : ['base','sale','purchase', 'account', 'analytic', 'mtsm_customization'],
    "author": "Zettatech",
    'summary': "add branch according to analytic distribution",
    "description": """ """,
    "website" : "https://odoo.zettatechmm.com",
    "data": [
            'security/ir_rules.xml',
            'data/data.xml',
            'views/analytic_distribution_view.xml',
            'views/sale_order_view.xml',
            'views/purchase_order_view.xml',
            'views/acc_banck_st_line_view.xml'
    ],
    'qweb': [
        # 'static/src/xml/template.xml',
    ],
    'license': 'LGPL-3',
    "auto_install": False,
    "installable": True,
    # 'assets': {
        
    # },
}
