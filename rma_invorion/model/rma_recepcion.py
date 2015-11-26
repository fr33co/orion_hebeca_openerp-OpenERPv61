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

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    _columns = {
    'invoice_refund': fields.boolean("Refund"),
    }
    
    _defaults = {
    'invoice_refund': False,
    }
    
    #~ Esta Funcion evita que al duplicar la factura se le coloque el mismo valor en el campo invoice_refund
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        if context is None:
            context = {}
        print context
        if context.get('rma_invoice_copy', False):
            default = default.copy()
            default.update({'invoice_refund':False })
            res = super(account_invoice, self).copy(cr, uid, id, default, context=context)
        else:
            raise osv.except_osv(_('Alert !'), _('No puede duplicar una factura.'))
        return res
        
account_invoice()

class rma_recepcion(osv.osv):
    _name = 'rma.recepcion'
    _description = 'Orden de recepcion'

    # Se determina el status de la garantia
    def status_warranty(self, cr, uid, ids, context = None):
        result = {}
        obj_brw = self.browse(cr, uid, ids)
        account_invoice = self.pool.get('account.invoice')
        ail_obj = self.pool.get('account.invoice.line')
        account_invoice_src = account_invoice.search(cr, uid, [], context=context)
        for rma in obj_brw:
            rma_invoice = rma.invoice_id.id
            account_invoice_rd = account_invoice.read(cr, uid, rma_invoice, ['origin', 'address_invoice_id', 'partner_id', 'internal_number', 'date_invoice', 'id'], context)
        
            #Obtengo el IMEI del producto
            ail_src = ail_obj.search(cr, uid, [('invoice_id', '=', account_invoice_rd['id'])])
            ail_brw = ail_obj.browse(cr, uid, ail_src)
            for get_code in ail_brw:
                for get_code2 in get_code.imei_ids:

                    # Se busca la factura de compra, generalmente sera el primer indice
                    fc_ail_src = ail_obj.search(cr, uid, [('imei_ids', '=', get_code2.id)])
                    fc_ail_rd = ail_obj.read(cr, uid, fc_ail_src, ['invoice_id', 'partner_id'], context)[0]
                    fc = fc_ail_rd.values()
                    fc_ai_rd = account_invoice.read(cr, uid, fc[0][0], ['origin', 'address_invoice_id'], context)

                    linea_imei = get_code2.imei_code
                    self.write(cr, uid, ids, {'origin': account_invoice_rd['origin'], 'internal_number': fc[0][1], 'customer_id': account_invoice_rd['partner_id'][1], 'address_invoice_id': account_invoice_rd['address_invoice_id'][1], 'imei_id': linea_imei, 'product': get_code.name, 'supplier_id': fc[1][1], 'origin_purchase': fc_ai_rd['origin'], 'address_invoice_id_supplier': fc_ai_rd['address_invoice_id'][1]})

        # Chequeo de garantia y condiciones del producto
        for l in obj_brw:
            # Se valida que solo se pueda realizar una vez el chequeo de garantia    
            if l.valid_warranty is False:
                if l.is_correct:
                    rc = account_invoice_rd['date_invoice']
                    rc_format = datetime.date(*map(int, rc.split('-')))
                    now = datetime.date.today().strftime('%Y-%m-%d')
                    now_format = datetime.date(*map(int, now.split('-')))
                    plus_warranty = rc_format+relativedelta(months=+6)
                    
                    # Se compara la fecha de venta con la fecha de hoy
                    if now_format >= plus_warranty:
                        self.write(cr, uid, ids, {'status_warranty': 'VENCIDA', 'valid_warranty': True, 'state': 'refused', 'date_recepcion': now_format, 'date_warranty': plus_warranty, 'claim_origine': 'w_expired'})
                    if now_format <= plus_warranty:
                        self.write(cr, uid, ids, {'status_warranty': 'DISPONIBLE', 'valid_warranty': True, 'state': 'confirmed','date_recepcion': now_format, 'date_warranty': plus_warranty})
                else:
                    raise osv.except_osv(_('Alert !'), _('No puede continuar con el proceso! No cumple con las condiciones de la garantia el producto.'))
            else:
                raise osv.except_osv(_('Alert !'), _('Ya se ha realizado el chequeo de garantia. Solo puede realizarla una vez.'))

    _columns = {
        'name': fields.char('Ref. Recepcion',size=24, required=True),
        'claim_origine': fields.selection([('none','No Especificado'),
                                    ('legal','Retractacion Legal'),
                                    ('w_expired','Garantia expirada'),
                                    ('cancellation','Cancelacion de Orden'),
                                    ('damaged','Producto dañado'),                                    
                                    ('exchange','Solicitud de Cambio'),
                                    ('other','Otro')], 'Motivo', required=True, help="Para describir el problema del producto"),
        'state' : fields.selection([('draft','Borrador'),
                                    ('refused','Rechazado'),
                                    ('confirmed','Confirmado'),
                                    ('in_to_control','Recepcion para control')], 'Estado', required=True),
        'applicable_guarantee': fields.selection([('none','No definida'),('us','Interna'),('supplier','Proveedor'),('brand','Marca fabricante')], 'Tipo de Garantia', required=True),
        'date_recepcion': fields.datetime('Fecha de Recepcion'),
        'date_warranty': fields.datetime('Fecha limite de Garantia'),
        'invoice_id': fields.many2one('account.invoice', 'Factura de venta', required=True),
        'journal_id': fields.many2one('account.journal', 'Diarios', required=True),
        'status_warranty': fields.char('Status de Garantia',size=64),
        'bateria': fields.boolean('Bateria'),
        'cargador': fields.boolean('Cargador'),
        'manos_libres': fields.boolean('Manos Libres'),
        'manual': fields.boolean('Manual'),
        'cable_usd': fields.boolean('Cable USB'),
        'audifonos': fields.boolean('Audifonos'),
        'microsd': fields.boolean('MicroSD'),
        'otros': fields.boolean('Otros'),
        'informacion_extra': fields.text('Informacion extra de los componentes del producto'),
        'is_correct': fields.boolean('Ud. considera que el producto cumple con las condiciones de garantia?', required=True),
        'origin': fields.char('Pedido de venta', size=64),
        'origin_purchase': fields.char('Pedido de compra', size=64),
        'internal_number': fields.char('Factura de compra',size=64),
        'product': fields.char('Producto',size=64),
        'product_id_exchange': fields.many2one('product.product', 'Producto a sustituir'),
        'imei_id_exchange': fields.many2one('product.product.lines', 'Codigo Imei a sustituir', domain="[('product_id', '=', product_id_exchange)]"),
        'customer_id': fields.char('Comprador',size=64),
        'supplier_id': fields.char('Proveedor',size=64),
        'tlf_contacto': fields.char('Telefono de contacto',size=64),
        'address_invoice_id': fields.char('Direccion del comprador',size=64),
        'address_invoice_id_supplier': fields.char('Direccion del proveedor',size=64),
        'imei_id': fields.char('Codigo Imei a recibir',size=64),
        'imei_id_exchange': fields.many2one('product.product.lines', 'Codigo Imei a sustituir', domain="[('product_id', '=', product_id_exchange)]"),
        'falla': fields.text('Falla del producto'),
        'responsible_id': fields.many2one('res.users', 'Responsable', required=True),
        'valid_warranty': fields.boolean('Validar chequeo de garantia'),
        'valid_return': fields.boolean('Validar devolucion de producto'),
        'invoice_return': fields.boolean('Factura Anulada'),
        'valid_change': fields.boolean('Validar cambio de producto'),
    }

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'rma.recepcion'),
        'invoice_return': False,
        'journal_id': 4,
    }


    def return_product(self, cr, uid, ids, context = None):
        wf_service = netsvc.LocalService("workflow")
        inv_obj = self.pool.get('account.invoice')
        imei_obj = self.pool.get("product.product.lines")
        rma_envio_obj = self.pool.get("rma.envio")
        attachment_obj = self.pool.get("ir.attachment")
        rma_brw = self.browse(cr, uid, ids, context)
        invoice_id = ''
        invoice_type = ''
        journal_id = ''
        imeis_ids = []
        for rma in rma_brw:
            if rma.is_correct is True: 
                    if rma.state == 'confirmed':
                            if rma.valid_return is False:
                                if not rma.invoice_return:
                                        invoice_id = rma.invoice_id.id

                                inv_brw = inv_obj.browse(cr, uid, [invoice_id], context)
                                for inv in inv_brw:
                                    for line in inv.invoice_line:
                                        if line.product_id.type_phone:
                                            for imei in line.imei_ids:
                                                imei_obj.write(cr, uid, imei.id, {'status':'Devuelto'})
                                envio_lines = {'supplier_id': rma.supplier_id,
                                                'rma_reference': rma.name,
                                                'date_recepcion': rma.date_recepcion,
                                                'imei_id': rma.imei_id,
                                                'origin': rma.origin_purchase,
                                                'invoice_supplier_id': rma.internal_number,
                                                'repair_state': 'confirmed',
                                                'address_invoice_id_supplier': rma.address_invoice_id_supplier,
                                                }
                                envio_lines_id = rma_envio_obj.create(cr, uid, envio_lines, context=context)
                                self.write(cr, uid, ids, {'valid_return': True})

                                # Se agrega el adjunto de la factura del proveedor como referencia
                                attach_fc_src = attachment_obj.search(cr, uid, [('res_name', '=', rma.internal_number)])
                                for int_attach_fc_src in attach_fc_src:
                                    attach_fc_cp = attachment_obj.copy(cr, uid, int_attach_fc_src, context=context)
                                attachment_obj.write(cr, uid, attach_fc_cp, {'res_model':'rma.envio','res_id': envio_lines_id}, context=context)
                            else:
                                raise osv.except_osv(_('Alert !'), _('Ya se ha realizado la devolucion del producto. Solo puede realizarla una vez.'))
                    else:
                        raise osv.except_osv(_('Alert !'), _('No puede continuar. La recepcion ha sido rechazada.'))
            else:
                raise osv.except_osv(_('Alert !'), _('No puede continuar. No ha realizado la validacion de garantia.'))
                                
                    
    def return_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wf_service = netsvc.LocalService("workflow")
        inv_obj = self.pool.get('account.invoice')
        imei_obj = self.pool.get("product.product.lines")
        rma_brw = self.browse(cr, uid, ids, context)
        
        invoice_id = ''
        invoice_type = ''
        journal_id = ''
        imeis_ids = []
        refund = False
        
        for rma in rma_brw:
            if rma.is_correct is True: 
                if rma.state == 'confirmed':
                    if not rma.invoice_return:
                        invoice_id = rma.invoice_id.id
                        invoice_type = rma.invoice_id.type
                        if rma.journal_id.type in ['purchase_refund','sale_refund']:
                            journal_id = rma.journal_id.id
                        else:
                            raise osv.except_osv(_('Alert !'), _('No puede continuar con el proceso! debe elegir un diario de devolucion.'))
                    else:
                        raise osv.except_osv(_('Alert !'), _('No puede continuar con el proceso! ya ha aplicado una devolucion de factura.'))
                else:
                    raise osv.except_osv(_('Alert !'), _('No puede continuar. La recepcion ha sido rechazada.'))
            else:
                raise osv.except_osv(_('Alert !'), _('No puede continuar. No ha realizado la validacion de garantia.'))
        
        inv_brw = inv_obj.browse(cr, uid, [invoice_id], context)
        for inv in inv_brw:
            if inv.invoice_refund:
                raise osv.except_osv(_('Alert !'), _('No puede continuar con el proceso! ya ha aplicado una devolucion de factura.'))
            for line in inv.invoice_line:
                if line.product_id.type_phone:
                    for imei in line.imei_ids:
                        imei_obj.write(cr, uid, imei.id,{'status':'Devuelto'})
                        
        context.update({'rma_invoice_copy':True,})
        if invoice_id and invoice_type:
            if invoice_type in ['in_invoice']:
                credit_id = inv_obj.copy(cr, uid, invoice_id, context=context)
                result = inv_obj.write(cr, uid, credit_id, {'type':'in_refund','parent_id':invoice_id,'journal_id':journal_id,}, context=context)
                wf_service.trg_validate(uid, 'account.invoice', credit_id, 'invoice_open', cr)
                inv_obj.write(cr, uid, invoice_id, {'invoice_refund':True,}, context=context)
            elif invoice_type in ['out_invoice']:
                credit_id = inv_obj.copy(cr, uid, invoice_id, context=context)
                result = inv_obj.write(cr, uid, credit_id, {'type':'out_refund','parent_id':invoice_id,'journal_id':journal_id,}, context=context)
                wf_service.trg_validate(uid, 'account.invoice', credit_id, 'invoice_open', cr)
                inv_obj.write(cr, uid, invoice_id, {'invoice_refund':True,}, context=context)
        else:
            raise osv.except_osv(_('Alert !'), _('No puede continuar con el proceso! No hay una factura asociada a la recepcion.'))
        
        return self.write(cr, uid, ids, {'invoice_return':True,}, context)


    def change_product(self, cr, uid, ids, context):
        obj_model = self.pool.get('ir.model.data')
        rma_brw = self.browse(cr, uid, ids, context)
        for rma in rma_brw:
            if rma.valid_change is False: 
                context.update({'imei_id': ids})
                return {
                            'view_type': 'form',
                            'view_mode':'form',
                            'res_model': 'return.product.rma.wizard',
                            'type': 'ir.actions.act_window',
                            'target': 'new',
                            'context': context,
                            'ref': 'rma_invorion.return_product_wizard_confirm'
                        }
            else:
                raise osv.except_osv(_('Alert !'), _('Ya se ha realizado un cambio de producto. Solo puede realizarla una vez.'))    
        
rma_recepcion()


class rma_envio(osv.osv):
    _name = 'rma.envio'
    _description = 'Orden de Envio'
    _columns = {
        'rma_reference': fields.char('Referencia de recepcion',size=64),
        'supplier_id': fields.char('Proveedor',size=64),
        'imei_id': fields.char('Codigo Imei',size=64),
        'invoice_supplier_id': fields.char('Factura de compra',size=64),
        'origin': fields.char('Pedido de Compra', size=64),
        'date_sendtoreopair': fields.datetime('Fecha de envio a reparacion'),
        'date_recepcion': fields.datetime('Fecha de recepcion'),
        'date_repaired': fields.datetime('Fecha de reparado'),
        'repair_state': fields.selection([
            ('draft','Borrador'),
            ('confirmed','Confirmado'),
            ('ready','Listo para reparar'),
            ('under_repair','En reparacion'),
            ('2binvoiced','Para ser facturado'),
            ('invoice_except','Excepcion de factura'),
            ('done','Hecho'),
            ('cancel','Cancelado')
            ], 'Estado', required=True),
        'address_invoice_id_supplier': fields.char('Direccion de Envio', size=64),
        'falla_cliente': fields.text('Proporcionado por el cliente'),
        'falla_responsable': fields.text('Proporcionado por el responsable'),
        'historial_ids': fields.one2many('rma.historial', 'historial_id', 'Historial'),
    }


    _order = "rma_reference"
    _rec_name = "rma_reference"

    def send_torepair(self, cr, uid, ids, context = None):
        wf_service = netsvc.LocalService("workflow")
        inv_obj = self.pool.get('account.invoice')
        imei_obj = self.pool.get("product.product.lines")
        rma_recepcion_obj = self.pool.get("rma.recepcion")
        rma_brw = self.browse(cr, uid, ids, context)
        now = datetime.date.today().strftime('%Y-%m-%d')
        now_format = datetime.date(*map(int, now.split('-')))
        for data in rma_brw:
            product_lines_src = imei_obj.search(cr, uid, [('imei_code', '=', data.imei_id)])
            imei_reparacion = {'status': 'Reparando'}
            imei_obj.write(cr, uid, product_lines_src, imei_reparacion, context=context)
            return self.write(cr, uid, ids, {'repair_state':'under_repair', 'date_sendtoreopair': now_format}, context)

            
    def product_repaired(self, cr, uid, ids, context = None):
        wf_service = netsvc.LocalService("workflow")
        inv_obj = self.pool.get('account.invoice')
        imei_obj = self.pool.get("product.product.lines")
        rma_recepcion_obj = self.pool.get("rma.recepcion")
        rma_brw = self.browse(cr, uid, ids, context)
        now = datetime.date.today().strftime('%Y-%m-%d')
        now_format = datetime.date(*map(int, now.split('-')))
        for data in rma_brw:
            product_lines_src = imei_obj.search(cr, uid, [('imei_code', '=', data.imei_id)])
            imei_reparacion = {'status': 'Disponible'}
            imei_obj.write(cr, uid, product_lines_src, imei_reparacion, context=context)
            return self.write(cr, uid, ids, {'repair_state':'done', 'date_repaired': now_format}, context)

                    
    def return_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wf_service = netsvc.LocalService("workflow")
        inv_obj = self.pool.get('account.invoice')
        imei_obj = self.pool.get("product.product.lines")
        rma_brw = self.browse(cr, uid, ids, context)
        
        invoice_id = ''
        invoice_type = ''
        journal_id = ''
        imeis_ids = []
        refund = False
        
        for rma in rma_brw:
            if rma.is_correct is True: 
                if rma.state == 'confirmed':
                    if not rma.invoice_return:
                        invoice_id = rma.invoice_id.id
                        invoice_type = rma.invoice_id.type
                        if rma.journal_id.type in ['purchase_refund','sale_refund']:
                            journal_id = rma.journal_id.id
                        else:
                            raise osv.except_osv(_('Alert !'), _('No puede continuar con el proceso! debe elegir un diario de devolucion.'))
                    else:
                        raise osv.except_osv(_('Alert !'), _('No puede continuar con el proceso! ya ha aplicado una devolucion de factura.'))
                else:
                    raise osv.except_osv(_('Alert !'), _('No puede continuar. La recepcion ha sido rechazada.'))
            else:
                raise osv.except_osv(_('Alert !'), _('No puede continuar. No ha realizado la validacion de garantia.'))
        
        inv_brw = inv_obj.browse(cr, uid, [invoice_id], context)
        for inv in inv_brw:
            if inv.invoice_refund:
                raise osv.except_osv(_('Alert !'), _('No puede continuar con el proceso! ya ha aplicado una devolucion de factura.'))
            for line in inv.invoice_line:
                if line.product_id.type_phone:
                    for imei in line.imei_ids:
                        imei_obj.write(cr, uid, imei.id,{'status':'Devuelto'})
                        
        context.update({'rma_invoice_copy':True,})
        if invoice_id and invoice_type:
            if invoice_type in ['in_invoice']:
                credit_id = inv_obj.copy(cr, uid, invoice_id, context=context)
                result = inv_obj.write(cr, uid, credit_id, {'type':'in_refund','parent_id':invoice_id,'journal_id':journal_id,}, context=context)
                wf_service.trg_validate(uid, 'account.invoice', credit_id, 'invoice_open', cr)
                inv_obj.write(cr, uid, invoice_id, {'invoice_refund':True,}, context=context)
            elif invoice_type in ['out_invoice']:
                credit_id = inv_obj.copy(cr, uid, invoice_id, context=context)
                result = inv_obj.write(cr, uid, credit_id, {'type':'out_refund','parent_id':invoice_id,'journal_id':journal_id,}, context=context)
                wf_service.trg_validate(uid, 'account.invoice', credit_id, 'invoice_open', cr)
                inv_obj.write(cr, uid, invoice_id, {'invoice_refund':True,}, context=context)
        else:
            raise osv.except_osv(_('Alert !'), _('No puede continuar con el proceso! No hay una factura asociada a la recepcion.'))
        
        return self.write(cr, uid, ids, {'invoice_return':True,}, context)


    def change_product(self, cr, uid, ids, context):
        obj_model = self.pool.get('ir.model.data')
        rma_brw = self.browse(cr, uid, ids, context)
        for rma in rma_brw:
            print rma.imei_id
        context.update({'imei_id': ids})
        return {
                    'view_type': 'form',
                    'view_mode':'form',
                    'res_model': 'return.product.rma.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': context,
                    'ref': 'rma_invorion.return_product_wizard_confirm'
                }
                
rma_envio()


class rma_historial(osv.osv):
    _name = 'rma.historial'
    _description = 'Historial'
    _columns = {
        'historial_id': fields.many2one('rma.envio', 'Historial', readonly=True),
        'date_historial': fields.datetime('Fecha'),
        'responsible_id': fields.many2one('res.users', 'Responsable', required=True),
        'short_title': fields.char('Titulo',size=64),
        'info': fields.text('Informacion'),
    }
    
rma_historial()
