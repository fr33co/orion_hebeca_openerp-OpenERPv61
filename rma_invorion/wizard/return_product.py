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

from osv import fields,osv
import netsvc
from datetime import datetime
import datetime
import time
from dateutil.relativedelta import relativedelta
from tools.translate import _
import decimal_precision as dp

class return_product_rma_wizard(osv.osv):
    _name = 'return.product.rma.wizard'

    def _get_imei(self, cr, uid, context):
        ids = context.get('imei_id', False)
        rma_rc_rd = self.pool.get('rma.recepcion').read(cr, uid, ids, ['imei_id'], context)[0]
        return rma_rc_rd['imei_id']

    def _get_product(self, cr, uid, context):
        ids = context.get('imei_id', False)
        rma_rc_rd = self.pool.get('rma.recepcion').read(cr, uid, ids, ['product'], context)[0]
        return rma_rc_rd['product']
        

    _columns = {
        'name': fields.char('Name', size=64),
        'product_id': fields.char('Producto recibido', size=64),
        'imei_id': fields.char('Codigo Imei recibido', size=64),
        'product_id_exchange': fields.many2one('product.product', 'Producto a sustituir'),
        'imei_id_exchange': fields.many2one('product.product.lines', 'Codigo Imei a sustituir', domain="[('product_id', '=', product_id_exchange)]"),
    }

    _defaults = {
        'imei_id': _get_imei,
        'product_id': _get_product,
    }

    def change_product(self, cr, uid, ids, context):
        obj_brw = self.browse(cr, uid, ids, context)
        rma_recepcion_obj = self.pool.get("rma.recepcion")
        product_lines_obj = self.pool.get("product.product.lines")
        ids = context.get('imei_id', False)
        for data in obj_brw:
            recepcion_update = {'product_id_exchange': data.product_id_exchange.id,
                                'imei_id_exchange': data.imei_id_exchange.id,
                                'valid_change': True,
                                                }
            rma_recepcion_obj.write(cr, uid, ids, recepcion_update, context=context)

            # Status de imei a Vendido - El que se entrega a cambio
            product_lines_src1 = product_lines_obj.search(cr, uid, [('id', '=', data.imei_id_exchange.id)])
            imei_replace = {'status': 'Vendido'}
            product_lines_obj.write(cr, uid, product_lines_src1, imei_replace, context=context)

            # Status de imei a Devuelto - El que se recibe para cambiar 
            rma_rc_rd = self.pool.get('rma.recepcion').read(cr, uid, ids, ['imei_id'], context)[0]
            product_lines_src2 = product_lines_obj.search(cr, uid, [('imei_code', '=', rma_rc_rd['imei_id'])])
            imei_recibe = {'status': 'Devuelto'}
            product_lines_obj.write(cr, uid, product_lines_src2, imei_recibe, context=context)
            
        return {'type':'ir.actions.act_window_close'}


return_product_rma_wizard()
