# -*- coding: utf-8 -*-

{
    'name': 'Gestión de RMA para Inversiones Orion',
    'version': '0.1',
    'category': 'RMA',
    'description': """
    Este Modulo permite la gestión de reparaciones de productos
    """,
    'author': "Angel A. Guadarrama B.",
    'website': 'http://fr33co.wordpress.com',
    'depends': ['base', 'product', 'sale', 'account', "procurement", "stock", "resource", "purchase", "product", "process",
    ],
    'update_xml': [
        'view/rma_recepcion_sequence.xml',
        'view/rma_recepcion_view.xml',
        'wizard/return_product_wizard_view.xml',
    ],
    'installable': True,
    'active': False,
}
