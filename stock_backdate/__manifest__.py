# -*- coding: utf-8 -*-

{
    "name" : "Stock Backdate",
    "version" : "17.0.0.0",    
    "depends" : ['base', 'stock'],
    "author": "Zettatech",
    'summary': "Stock Backdate",
    "description": """    
	
    """,   
    "data": [
        "security/sh_stock_backdate_groups.xml",   
        "security/ir.model.access.csv",         
        "wizard/sh_picking_backdate_wizard_views.xml" ,
        # "wizard/sh_scrap_backdate_wizard_views.xml",      
        "data/stock_picking_data.xml",
        # "data/stock_scrap_data.xml",            
        # "views/res_config_settings_views.xml",
        # "views/stock_move_line_views.xml",   
        # "views/stock_move_views.xml",   
        # "views/stock_picking_views.xml",  
        # "views/stock_scrap_views.xml", 
    ],    
    'license': "LGPL-3",   
    
}
