# -*- coding: utf-8 -*-
{
    'name': 'Partner Customization',
    'version': '1.2',
    'summary': 'Base setup module for partner.',
    'description': """
       Township & City/Village in contact form.
    """,
    'category': 'Setup',
    'author': "Moe Pa Pa",
    'website': "www.moepapaplanet.com",
    'license': "LGPL-3",
    'depends': [
        'contacts',
        'base',
        'crm',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_township_view.xml',
        'views/city_village_view.xml',
        'views/res_partner_view.xml',
        'views/partner_request_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
