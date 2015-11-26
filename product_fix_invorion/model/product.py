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


from osv import fields, osv
from tools.translate import _


class product_product_lines(osv.osv):
    _name = 'product.product.lines'


    def _get_product(self, cr, uid, context=None):
        res = {}
        product = self.pool.get('product.product').search(cr, uid, [('active', '=' ,True)])
        if product:
            product_br = self.pool.get('product.product').browse(cr, uid, product[0], context=None)
            ret = product_br.id
        return ret
        

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'imei_code': fields.char('Codigo IMEI', size=256, required=False, readonly=True),
        'status': fields.selection([
            ('Disponible', 'Disponible'),
            ('Vendido', 'Vendido'),
            ('Devuelto', 'Devuelto'),
            ('Cambiado', 'Cambiado'),
            ('Reparando', 'En Reparacion'),
            ('Reparado', 'Reparado'),
        ], 'Status', readonly=True, required=True, help="Este estatus diferencia los imeis por su estado."),
    }
    
    _order = "status"
    _rec_name = "imei_code"
    _defaults = {
        'product_id': _get_product,
    }
    
product_product_lines()

class product_product(osv.osv):
    _inherit = 'product.product'
    _columns = {
        'product_ids': fields.one2many('product.product.lines', 'product_id', 'Lineas de Productos'),
        'type_phone': fields.boolean('Es un Telefono', help='Debera Marcar si el producto es un telefono'),
    }
    
    _defaults = {
    'type_phone': True,
    }
product_product()

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'product_ids': fields.one2many('product.product.lines', 'partner_id', 'Lineas de Productos'),
    }
res_partner()
