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

from osv import osv
from osv import fields
import base64
from tools.translate import _
import binascii
from StringIO import StringIO
import csv
import time
from datetime import datetime
import xmlrpclib


#----------------------------------------------------------
# Stock Picking
#----------------------------------------------------------
class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _columns = {
        'file': fields.binary('Archivo a cargar'),
        'data_charged': fields.boolean('Data Cargada'),
    }
   
    def get_id_(self, cr, uid, values,obj,field):
        """
        Busca el id de un objeto que se le pase por [obj], donde se cumpla que la 
        variable [field] igual a la variable [values]
        """
        ids = self.pool.get(obj).search(cr,uid,[(str(field),'=',str(values))])
        if ids:
            return int(ids[0])
        else:
            return 0
            
    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            seq_obj_name =  'stock.picking.' + vals['type']
            vals['name'] = self.pool.get('ir.sequence').get(cr, user, seq_obj_name)
        new_id = super(stock_picking, self).create(cr, user, vals, context)
        return new_id
        
    def upload_imei(self, cr, uid, ids, context=None):
        """
        Funcion para la carga del comprobante contable, en el proceso primero se
        sube el archivo a la base de datos para despues ser extraido, convertido
        en un archivo virtual que sera procesado en dos pasos, primero carga del
        account.move y despues account.move.line.
        """
        if context is None:
            context = {}
        #~ print "Esto son los IDs ", ids
        record_id = self.browse(cr, uid, ids, context=context)
        #~ print "RECORD_ID", record_id
        

        #Modelos necesarios
        obj_product = self.pool.get('product.product')
        obj_product_lines = self.pool.get('product.product.lines')
    
        file_in = record_id[0].file
        #~ print "Este es el archivo ", file_in
        
        #Se convierte el archivo de binario a lectura estandar y despues se
        #pasa a un archivo virtual
        imei_csv = binascii.a2b_base64(unicode(file_in))
        arch_csv = StringIO(imei_csv)
        
        # Busqueda de lineas de imei y sus codigos
        imeis_lines = obj_product_lines.search(cr, uid, [], context=context)
        imeis_codes = obj_product_lines.browse(cr, uid, imeis_lines)
        
        
        #INICIAL VALIDACION DEL ARCHIVO
        f_move = csv.DictReader(arch_csv, delimiter=';')
        for row in f_move:        
            # Validacion para busqueda de imeis existentes en la base de datos
            for p in imeis_codes:
                if p.imei_code == row['imei_code']:
                    raise osv.except_osv(_('Alert !'), _('Al menos un codigo imei en el csv existe en la base datos!'))

        #Se convierte el archivo de binario a lectura estandar y despues se
        #pasa a un archivo virtual
        imei_csv = binascii.a2b_base64(unicode(file_in))
        arch_csv = StringIO(imei_csv)

        #INICIAL VALIDACION DEL ARCHIVO
        f_move = csv.DictReader(arch_csv, delimiter=';')
        lineas = 0
        fallo = False
        imei_code = ""
        reference = ""
        qty_dic = {}
        try:
            for row in f_move:
                
                if row['reference'] == reference:
                    qty_dic[row['reference']] += 1.0
                elif not qty_dic.get(row['reference'], False):
                    qty_dic.update({row['reference']:1.0})
                else:
                    qty_dic[row['reference']] += 1.0
                """Se asigna cada cabecera a una variable para validar que este
                en el formato correcto"""
                imei_code = row['imei_code']
                reference = row['reference']

                if not (imei_code, reference):
                    fallo = True
        except Exception, e:
            raise osv.except_osv(_('Error !'), _("Verificar que el archivo sea un CSV.\nLa cabecera tenga el formato: imei_code; referencia.\n Error con: %s")%(e))
        
        print "Este es el diccionario ", qty_dic
        if fallo:
            raise osv.except_osv(_('Error !'), _("Hay campos vacios en el CSV. Revise!"))
        
        # Validacion para que data se carge una vez
        ### Cambiar a TRUE al terminar de arreglar
        if record_id[0].data_charged != True:

            # Se busca el id de las lineas de stock.move
            res = {}
            stock_picking_id = self.search(cr, uid, [('id', '=', ids)])
            sm_src = self.pool.get('stock.move').search(cr, uid, [('picking_id', '=', stock_picking_id)])
            sm_brw = self.pool.get('stock.move').browse(cr, uid, sm_src)
            print "Este es el Browse ", sm_brw
            
            for stock_lines in sm_brw:
                
                # Validamos los imeis almacenados no sean iguales a los del csv
                #Se convierte el archivo de binario a lectura estandar y despues se
                #pasa a un archivo virtual
                imei_csv = binascii.a2b_base64(unicode(file_in))
                arch_csv = StringIO(imei_csv)
                
                #INICIAL VALIDACION DEL ARCHIVO
                f_move = csv.DictReader(arch_csv, delimiter=';')
                
                for row in f_move:
                    ####################################################
                    # Validacion para realizar chequeo que Lineas de archivo = cantidad de productos
                    # Buscamos las cantidades compradas - int(stock_lines.product_qty)
                    print "Esto es stock_lines.product_id.default_code ", stock_lines.product_id.default_code
                    print "Esto es qty_dic[stock_lines.product_id.default_code] ", qty_dic[stock_lines.product_id.default_code]
                    print "Esto es stock_lines.product_qty ", stock_lines.product_qty
                    if int(qty_dic[stock_lines.product_id.default_code]) != int(stock_lines.product_qty):
                        print 'No son iguales'
                        raise osv.except_osv(_('Alert !'), _('La cantidad de codigos IMEI en el csv no concuerdan con las cantidad de productos comprados!'))

                    ####################################################
                    # Validamos que el default_code concuerden con los del csv
                    # Buscamos las referencias de los producto - stock_lines.product_id.default_code
                    if stock_lines.product_id.default_code == row['reference']:

                        # Se arma la linea y se escribe en la tabla
                        # Buscamos id del producto - stock_lines.product_id.id
                        # Buscamos partner del producto - stock_lines.partner_id.id
                        product_lines_data = {
                            'product_id' : stock_lines.product_id.id,
                            'partner_id' : stock_lines.partner_id.id,
                            'imei_code' : row['imei_code'],
                            'status' : 'Disponible',
                                        }
                        print "product Lines ", product_lines_data
                        product_lines_id = obj_product_lines.create(cr, uid, product_lines_data,context)
                        message = _("Data Cargada!.")
                        stock_picking_write = self.write(cr, uid, stock_picking_id, {'data_charged': True})
                        self.log(cr, uid, stock_picking_write, message, context=context)
            # Se llama a action_process de stock_picking
            return self.action_process(cr, uid, ids, context=context)
        else:
            raise osv.except_osv(_('Alert !'), _('Ya se ha cargado data. Solo puede hacerlo una vez por entrada de albaran!'))
            
stock_picking()
