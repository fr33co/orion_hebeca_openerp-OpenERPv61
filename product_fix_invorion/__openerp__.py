# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Product Fix for Inversiones Orion',
    'version': '1.0',
    'category': 'Generic Modules/Product',
    'description': """
    Este modulo añade a la vista de producto una pagina con las caracteristicas
    del telefono y las lineas de productos (product_id, partner_id, imei_code, status). 
    """,
    'author': 'Angel A. Guadarrama B.',
    'website': 'http://fr33co.wordpress.com',
    'depends': ['product'],
    'init_xml': [],
    'update_xml': [
        'view/product_view.xml',
        'security/product_fix_security_invorion.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'active': False,
}
