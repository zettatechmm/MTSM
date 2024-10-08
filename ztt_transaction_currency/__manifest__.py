# -*- coding: utf-8 -*-

{
    "name" : "ZTT Transaction Currency",
    "version" : "17.0.0.1",
    "category" : "Currency",
    "depends" : ['base','sale','purchase','sale_renting', 'account', 'stock', 'sale_stock', 'stock_account', 'purchase_stock', 'mtsm_customization'],
    "author": "Zettatech",
    'summary': "Sale Customization",
    "description": """
    
    Purpose :
        1. add field "Currency Rate" (currency_rate, float) on the following form
            Sales Order Form
            Customer Invoice
            Credit Notes
            Purchase Order Form
            Stock Receipt (valuation calculation based on the transaction currency rate)
            Vendor Bill
            Refund
            Payment Form (Customer / Vendor)
            Bank Statement Form (cashbook / bank book, account.bank.statement.line)
            Register Payment Wizard form (account.payment.register.form)
	
    """,

    "website" : "https://odoo.zettatechmm.com",
    "data": [
        'views/views.xml',
        'views/banck_st_line_view.xml',
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
