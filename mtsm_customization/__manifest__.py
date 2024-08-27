# -*- coding: utf-8 -*-

{
    "name" : "MTSM Customization",
    "version" : "17.0.0.0",
    "category" : "mtsm_customization",
    "depends" : ['base','sale','purchase','sale_renting', 'stock', 'sale_stock'],
    "author": "Zettatech",
    'summary': "MTSM Custom Feature",
    "description": """""",
    "website" : "https://odoo.zettatechmm.com",
    "data": [
        'data/ir_sequence_data.xml',
        'security/ir_rules.xml',
        'views/ir_sequence_view.xml',
        'views/views.xml',
        'report/delivery_slip_report.xml',
        'report/inherit_report_invoice.xml',
        'report/inherit_sale_report.xml',
    ],
    'qweb': [
        # 'static/src/xml/template.xml',
    ],
    'license': "LGPL-3",
    "auto_install": False,
    "installable": True,
    # 'assets': {
        
    # },
}
