# -*- coding: utf-8 -*-

{
    'name': 'Gestion de Ventas',
    'version': '0.1',
    'category': 'Sales & Purchases',
    'description':' ',
    'author': 'Industrias Diana, C.A.',
    'website': 'http://www.industriasdiana.gob.ve',
    'depends': ['sale',
                'stock',
                'account_voucher',
                'l10n_ve_fiscal_requirements',
                'l10n_ve_withholding_islr',
    ],
    'update_xml': [
                'view/sales_view.xml',
    ],
    'data': [
    ],
    'installable': True,
    'active': False,
}
