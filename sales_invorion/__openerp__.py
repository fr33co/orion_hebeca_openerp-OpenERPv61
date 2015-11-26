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
                'product_fix_invorion',
                'partner_fix_search_invorion',
    ],
    'update_xml': [
                'view/sales_view.xml',
                'view/inherit_account_invoice.xml',
    ],
    'data': [
    ],
    'installable': True,
    'active': False,
}
