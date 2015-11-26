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
    'name': 'Wizard Stock picking fix for Inversiones Orion',
    'version': '1.0',
    'category': 'Stock',
    'description': """
    This module adds a new page for upload digital documents 
    """,
    'author': 'Angel A. Guadarrama B.',
    'website': 'http://fr33co.wordpress.com',
    'depends': ['stock'],
    'init_xml': [],
    'update_xml': [
        'view/stock_picking_invorion.xml',
    ],
    'installable': True,
    'active': False,
}
