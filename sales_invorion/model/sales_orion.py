# -*- coding: utf-8 -*-
"""
Módulo utilizado para adaptar el módulo de ventas de Industrias Diana
"""

import time
import netsvc
from osv import fields, osv
from tools import config
from tools.translate import _

class sale_order(osv.osv):
    _inherit = "sale.order"

    _defaults = {
        'name':'/',
    }
    

    def create(self, cr, uid, values, context=None):

        res = super(sale_order, self).create(cr, uid, values, context)
        values = {
            'name':self.pool.get('ir.sequence').get(cr, uid, 'sale.order')
            }
        seq = self.write(cr, uid, res, values, context)
        
        if not seq:
            raise osv.except_osv(_('Error!'),_('Hubo error en el proceso de creacion de la secuencia. Contactar el administrador!'))
    
        return res
        
    def write(self, cr, user, ids, vals, context=None):
        
        if vals.get('partner_id',False) and vals.get('pricelist_id',False):
            so_brow = self.browse(cr,user,ids)
            if so_brow[0].order_line:
                raise osv.except_osv(_('Error!'),_('Hubo cambio de cliente y tarifas. Debe: 1ro eliminar las lineas del pedido y luego presionar guardar y editar para realizar el registro!'))
        
        record = super(sale_order, self).write(cr, user, ids, vals, context)
        
        return record
    
    def copy(self, cr, uid, id, defaults, context=None): #Sobreescritura del metodo copy para no permitir duplicar objetos stock_picking
        raise osv.except_osv(_('Acción Denegada!'),_('No se permite duplicar Pedidos!'))
        return False
    
    def check_limit(self, cr, uid, ids, context={}):
        if context is None:
            context = {}
        
        ##############################################################################################################
        #Se verifica si hay lineas en el pedido de venta
        ##############################################################################################################
        obj_so_lines = self.pool.get('sale.order.line')
        so_lines = obj_so_lines.search(cr, uid, [('order_id', '=', ids[0])])
        
        if not so_lines:
            raise osv.except_osv(_('Error !'), _('Por favor ingresar las líneas del pedido de venta antes de continuar!'))
            return False
        ###############################################################################################################
        
        #lineas del pedido
        br_so_lines = obj_so_lines.browse(cr, uid, so_lines, context)
        
        #############################################################################################################
        #Se verifica esta asociado el producto en cada linea del pedido
        #############################################################################################################
        existe_producto = True
        for linea in br_so_lines:
            if not linea.product_id:
                existe_producto = False
                break
        if not existe_producto:
            raise osv.except_osv(_('Error !'), _('No se puede procesar el pedido. No hay producto asociado en alguna de las lineas.!'))
            return False
        #############################################################################################################

    def onchange_partner_id(self, cr, uid, ids, part):
        so_onchange_partner_id = super(sale_order, self).onchange_partner_id( cr, uid, ids, part)
        address_obj = self.pool.get('res.partner.address')
        if so_onchange_partner_id['value'].get('partner_order_id',False):
            #si existe un contacto, verificar si es el unico contacto, de lo contrario asignar False
            contacto = address_obj.search(cr,uid,[('partner_id','=',part),('type','=','contact')])
            if len(contacto) > 1:
                so_onchange_partner_id['value']['partner_order_id'] = False
                
        if so_onchange_partner_id['value'].get('partner_shipping_id',False):
            #si existe un contacto, verificar si es el unico conctacto, de lo contrario asignar False
            contacto = address_obj.search(cr,uid,[('partner_id','=',part),('type','=','delivery')])
            if len(contacto) > 1:
                so_onchange_partner_id['value']['partner_shipping_id'] = False
  
        return so_onchange_partner_id
        
    def action_wait(self, cr, uid, ids, *args):
        self.check_limit(cr, uid, ids,context=None)
        res = super(sale_order,self).action_wait(cr, uid, ids, *args)
        return True
        
sale_order()


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    """ OJO: Debo agregar una columna para el imei y enlazarlos a la factura, a su vez
    se debe agregar un estado para saber cual esta disponible y cual no debe estar 
    disponible"""
    
    #Validaciones tanto para crear como para actualizar
    def validaciones_registros(self,values):
        
        if values.get('type',False):
            if values['type'] != 'make_to_stock':
                raise osv.except_osv(_('Error!'),_('Debe indicar el metodo de abastecimiento desde stock !'))

        return True
        
    
    def create(self, cr, uid, values, context=None):
        
        self.validaciones_registros(values)
        self.stock_picking_verify(cr, uid, values, context)
        res = super(sale_order_line, self).create(cr, uid, values, context)
        
        return res
        
    def write(self, cr, user, ids, vals, context=None):
        
        self.validaciones_registros(vals)
        
        record = super(sale_order_line, self).write(cr, user, ids, vals, context)
        
        return record

    def stock_picking_verify(self, cr, uid, values, context=None):
        
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        
        product_obj = product_obj.browse(cr, uid, values['product_id'], context) 
        
        uom2 = product_obj.uom_id
        if (product_obj.type=='product') and (product_obj.virtual_available * uom2.factor < values['product_uom_qty'] * product_obj.uom_id.factor) \
          and (product_obj.procure_method=='make_to_stock'):
                raise osv.except_osv(_('Invalid action !'), _('No puede vender un producto que no tiene existencia !'))
        return True
        
sale_order_line()

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    
    _order = "id desc"
    
stock_picking()

class stock_move(osv.osv):
    _inherit = "stock.move"
    
        
stock_move()


class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    
    def validar_concept_id_account_invoice_line(self, cr, uid, ids):
        """Funcion para validar que la factura no se le apruebe si unas de las
        lineas de la factura no tiene retencion asociada al menos que sea una factura de venta."""
        ai_brw = self.browse(cr, uid, ids)
        if ai_brw[0].type not in ('out_invoice','out_refund'):
            for ail in ai_brw[0].invoice_line:
                if not ail.concept_id :
                    raise osv.except_osv(_('Error con Retenciones'),_("Debe registrar el tipo de retencion en cada linea de la factura."))
        return True
    
    def validar_imeis(self, cr, uid, ids, context=None):
        """Funcion para validar que la factura no se le apruebe si unas de las
        lineas de la factura no tiene retencion asociada al menos que sea una factura de venta."""
        ai_brw = self.browse(cr, uid, ids,context)
        for ai in ai_brw:
            for ail in ai.invoice_line:
                if ail.product_id.type_phone:
                    if len(ail.imei_ids) != ail.quantity:
                        raise osv.except_osv(_('IMEI Error'),_("Debe registrar la misma cantidad de imeis y telefonos vendidos."))
        return True
    
    def update_imeis(self, cr, uid, ids, context=None):
        """Funcion para escribir el cambio de estado  del imei al
        aprobar la factura"""
        imei_obj = self.pool.get("product.product.lines")
        ai_brw = self.browse(cr, uid, ids,context)
        for ai in ai_brw:
            for ail in ai.invoice_line:
                if ail.product_id.type_phone:
                    for imei in ail.imei_ids:
                        imei_obj.write(cr, uid, imei.id,{'status':'Vendido'})
        return True
    
    def action_date_assign(self, cr, uid, ids, *args):
        #Se hereda la función action_date_assign para llamar funcion de validacion
        self.validar_concept_id_account_invoice_line(cr, uid, ids)
        return super(account_invoice, self).action_date_assign(cr, uid, ids, args)
    
    def action_number(self, cr, uid, ids, context=None):
        inv_brw = self.browse(cr, uid, ids, context)
        for ai in inv_brw:
            if ai.type in ('out_invoice'):
                self.validar_imeis(cr, uid, ids, context)
                self.update_imeis(cr, uid, ids, context)
        return super(account_invoice, self).action_number(cr, uid, ids, context)
    
    _columns = {
        'sale_ids': fields.many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', 'Sale Orders', help='This is the list of sale orders that generated this invoice'),
        'address_shipping_id': fields.many2one('res.partner.address', 'Invoice Address', readonly=True, states={'draft':[('readonly',False)]}),
    }
    
    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        
        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        
        partner = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['delivery'])
        shipping_addr_id = partner['delivery']
        
        result['value']['address_shipping_id'] = shipping_addr_id
        
        
        
        return result
    
account_invoice()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    
    _columns = {
    'imei_ids': fields.many2many('product.product.lines','product_product_lines_rel','line_id','imei_id','Imeis Telefonicos', help='This is the list of imei that you choose'),
    'imei_gun': fields.char('Añadir IMEI con pistola', size=64),
    }
    
    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = []
        res = super(account_invoice_line,self).move_line_get(cr, uid, invoice_id, context=context)
        return res

    def imei_process(self, cr, uid, ids, context=None):
        obj_brw = self.browse(cr, uid, ids)
        product_lines_obj = self.pool.get('product.product.lines')
        for imei in obj_brw:
            add_imei = imei.imei_gun
            print add_imei
            imei_src = product_lines_obj.search(cr, uid, [('imei_code', '=', add_imei)])
            print imei_src
    
account_invoice_line()
