# -*- coding: utf-8 -*-
#############################################################################

{
    'name': "UOM In PriceList",
    'version': '17.0.1.0.0',
    'category': "Extra Tools",
    'summary': """This module will helps to add Unit of Measure condition in 
    the advanced Price list rule""",
    'description': """Unit of measure in the price list rule. This module will
    help set the UOM rule in the price list. And it can be applied to the 
    advanced price rule and used in the sale order.""",
    'author': 'Ztt-Dev',
    'company': 'Zettatech Myanmar',
    'maintainer': 'Zettatech Myanmar',
    'website': "https://odoo.zettatechmm.com",
    'depends': ['sale_management', 'product'],
    'data': ['views/product_pricelist_item_views.xml'],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
