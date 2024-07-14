# -*- coding: utf-8 -*-
#############################################################################
#
#    Muhammad Irfan Mauly 
#
#    Copyright (C) 2020-TODAY Muhammad Irfan Mauly 
#
#############################################################################
{
    'name': 'Daily Report Inventory',
    'version': '13.0.5.0.0',
    'summary': """ Daily Report Inventory""",
    'description': """ Daily Report Inventory """,
    'category': '',
    'author': 'Irfan',
    'company': 'Irfan',
    'maintainer': 'Irfan',
    'depends': ['base', 'stock'],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'report/report_daily_inventory_template.xml',
        'report/view_daily_report_stock.xml',
        'views/stock_location_views.xml',
        'wizard/views_daily_report_inventory.xml',
    ],
    'images': [],
    'license': 'LGPL-3',
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}