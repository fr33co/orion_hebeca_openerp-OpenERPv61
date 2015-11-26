# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2011 Kadima Developers, C.A. (http://www.kadima.com.ve)
# All Rights Reserved.
# Programmed by: Jose Moreno (desarrollo@kadima.com.ve)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
###############################################################################
from osv import osv
from osv import fields
import netsvc
import base64
from tools.translate import _
import unicodedata 
import time
import datetime
import paramiko
import logging

def elimina_tildes(s):
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


class pos_sale_printer(osv.osv):
    _name = "pos.sale.printer"
    
    _columns = {
            'name': fields.char("Nombre Impresora",size=128, required=True),
            'ip_address': fields.char("Direccion IP",size=128, required=True),
            'machine_user': fields.char("Usuario Remoto",size=128, required=True),
            'machine_pass': fields.char("Password Remoto",size=128, required=True),
            'ssh_port': fields.char("Puerto SSH",size=128, required=True),
            'command': fields.char("Aplicacion a Ejecutar",size=128, required=True),
            'local_dir': fields.char("Directorio Local",size=128, required=True),
            'upload_dir': fields.char("Directorio Remoto",size=128, required=True),
            'state': fields.selection([
            ('online', 'Activa'),
            ('offline', 'Inactiva')
        ], 'Estado', required=True, help="Estado de la impresora fiscal.",readonly=True),
    }
    
    _defaults = {
        'state':'offline',
    }

    def online_fiscal_point(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        online = []
        point_ids = self.search(cr, uid, [('state','=','online')])
        #~ online = [ p for p in self.browse(cr, uid, point_ids, context) if p.state == 'online']
        if len(online) > 1:
            raise osv.except_osv(_('Invalid action !'), _('En esta version no puede activar mas de una impresora fiscal al mismo tiempo!')) 
        return self.write(cr, uid, ids, {'state':'online'}, context)
    
    def offline_fiscal_point(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'offline'}, context)
pos_sale_printer()

class account_tax(osv.osv):
    _inherit = 'account.tax'
    
    _columns = {
        'print_character': fields.char("Representacion en la Impresora Fiscal",size=3),
    }
    
account_tax()

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _logger = logging.getLogger('account.invoice')
    
    _columns = {
    'account_invoice_payments_lines_ids':fields.one2many('account.invoice.payment.lines','invoice_id','Tipos de Pago'),
    'fiscal_voucher': fields.boolean("Impresion Fiscal"),
    }
    
    _defaults ={
    'fiscal_voucher':False,
    }
    
    def ssh_execute(self, cr, uid, ids, filename, context=None):
        #~ Ejecuta el Comando Remoto - Execute The Remote Command
        pof_obj = self.pool.get('pos.sale.printer')
        pof_act = pof_obj.search(cr, uid,[('state','=','online')])
        pof_brw = pof_obj.browse(cr, uid, pof_act)
        self._logger.info("SSH Exec: Inicio de la ejecusion del proceso.")
        for fiscal in pof_brw:
            server, user, passw, cmd, filepath, localpath = fiscal.ip_address, fiscal.machine_user, fiscal.machine_pass, fiscal.command, fiscal.local_dir, fiscal.upload_dir
        #~ Envia el Archivo por FTP
        self._logger.info("SFTP Exec: Inicio de la ejecusion del proceso SFTP.")
        transport = paramiko.Transport((server,22))
        transport.connect(username=user,password=passw)
        self._logger.info("SFTP Exec: Inicion de sesion en el host exitosa.")
        sftp = paramiko.SFTPClient.from_transport(transport)
        #~ Completa la ruta de los archivos
        filepath = filepath+filename
        localpath = localpath+filename
        self._logger.info("SFTP Exec: Comenzando el envio de datos al host.")
        sftp.put(filepath, localpath)
        sftp.close()
        transport.close()
        self._logger.info("SFTP Exec: Datos enviados con exito al host.")
        #~ Fin de Transferencia FTP
        
        #~ Crea el Objecto para la conexion ssh
        self._logger.info("SSH Exec: Inicio de sesion en el host remoto.")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #~ Se conecta al equipo remoto via ssh
        ssh.connect(server, username=user,password=passw)
        self._logger.info("SSH Exec: Ejecutando Comando.")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        self._logger.info("SSH Exec: Comando Ejecutado con exito.")
        ssh.close()
        self._logger.info("SSH Exec: El Proceso de Impresion ha sido exitoso.")
        #~ Fin del Bloque de conexion ssh
        return True
        
    #~ Comentada porque es para crear archivo Bematech
    #~ def fiscal_file_create(self, cr, uid, ids, context=None):
        #~ #~  Crea la Nota de Credito ó Factura - Create the Credit Note
        #~ pos_brw = self.browse(cr, uid, ids)
        #~ tax = 0.00
        #~ #~ Extrae la direccion local donde se creara el archivo
        #~ pof_obj = self.pool.get('pos.sale.printer')
        #~ pof_act = pof_obj.search(cr, uid,[('state','=','online')])
        #~ pof_brw = pof_obj.browse(cr, uid, pof_act)
        #~ for fiscal in pof_brw:
            #~ local_dir = fiscal.local_dir
        #~ for pos_reg in pos_brw:
            #~ num = str(pos_reg.id)
            #~ arch = "NC"+num+".FC"
            #~ try:
                #~ inv = open(local_dir+arch,"w")
                #~ print pos_reg.partner_id.name
                #~ print pos_reg.partner_id.vat[3:]
                #~ print arch
                #~ pago = "%.2f"%pos_reg.amount_total
                #~ pago = pago.replace(".",",")
                #~ inv.write(pos_reg.type+";"+elimina_tildes(pos_reg.partner_id.name)+";"+pos_reg.partner_id.reference+";"+pago+"\r\n")
                #~ for line in pos_reg.invoice_line:
                    #~ for tax in line.product_id.taxes_id:
                        #~ if tax.amount > 0.00:
                            #~ tax = int(line.product_id.taxes_id.amount * 10000)
                            #~ print "Este es el Impuesto", tax
                            #~ tax = str(tax)
                            #~ if len(tax) < 4:
                                #~ tax = "0"+tax
                                #~ print tax 
                        #~ else:
                            #~ tax = "FF"
                            #~ print tax
                    #~ code = line.product_id.default_code or "-"
                    #~ price = "%.2f"%line.price_unit
                    #~ price = price.replace(".",",")
                    #~ qty = int(line.quantity)
                    #~ qty = str(qty)
                    #~ linea = code +";"+elimina_tildes(line.product_id.name)+";"+tax+";"+"I"+";"+qty+";"+price+";%;0000\r\n"
                    #~ inv.write(linea)
                    #~ print "Invoice OK" 
                #~ inv.close()
            #~ except IOError as e:
                #~ raise osv.except_osv(_('Error !'), _('Message: %s'%e))
        #~ return arch

    def fiscal_file_create(self, cr, uid, ids, context=None):
        #~ Crea la Nota de Credito ó Factura - Create the Credit Note
        pos_brw = self.browse(cr, uid, ids)
        tax = 0.00
        #~ Extrae la direccion local donde se creara el archivo
        ail_obj = self.pool.get('account.invoice.line')
        pof_obj = self.pool.get('pos.sale.printer')
        pof_act = pof_obj.search(cr, uid,[('state','=','online')])
        pof_brw = pof_obj.browse(cr, uid, pof_act)
        
        local_dir = None
        
        for fiscal in pof_brw:
            local_dir = fiscal.local_dir
            
        if not local_dir:
            raise osv.except_osv(_('Error !'), _('Hay una impresora configurada o no se encuentra activa'))
            
        for pos_reg in pos_brw:
            num = str(pos_reg.id)
            arch = "FAC"+num+".FC"
            try:
                inv = open(local_dir+arch,"w")
                #~ print pos_reg.partner_id.name
                #~ print pos_reg.partner_id.vat[3:]
                print arch
                inv.write('e'+"\r\n")
                inv.write('i01NOMBRE/RAZ: '+elimina_tildes(pos_reg.partner_id.name)+"\r\n")
                #~ inv.write('i02RIF/CED: '+pos_reg.partner_id.vat[2:]+"\r\n")
                inv.write('i02RIF/CED: '+pos_reg.partner_id.ref+"\r\n")
                inv.write('i03REFERENCIA: '+pos_reg.number+'\r\n')
                for line in pos_reg.invoice_line:
                    iva = " "
                    for tax in line.invoice_line_tax_id:
                        iva = tax.print_character

                    code = line.product_id.default_code or "-"
                    print code
                    print "Este es el IVA:["+iva+"]"
                    # Crea el formato para le precio
                    price = line.price_unit
                    print price
                    price_dec = str(price-int(price))[1:]
                    price_dec1 = str(int(price_dec.replace('.', ''))).rjust(2, '0')
                    price_int = int(price)
                    price_int1 = str(price_int).rjust(8, '0')
                    price_format = str(price_int1) + str(price_dec1)
                            
                    # Crea el formato para las cantidades
                    qty = line.quantity 
                    qty_format1 = str(int(qty)).rjust(5, '0')
                    qty_format2 = str(qty_format1.ljust(8, '0'))
                    
                    # Escribo la linea en el archivo
                    if pos_reg.type in ('out_refund'):
                        linea = 'd'+iva+price_format+qty_format2+elimina_tildes(line.product_id.name)+' Cod: '+code+"\r\n"
                    elif pos_reg.type in ('out_invoice'):
                        linea = iva+price_format+qty_format2+elimina_tildes(line.product_id.name)+' Cod: '+code+"\r\n"
                    inv.write(linea)

                    #Obtengo el IMEI del producto
                    acl_src = ail_obj.search(cr, uid, [('id', '=', line.id)])
                    acl_brw = self.pool.get('account.invoice.line').browse(cr, uid, acl_src)
                    for get_code in acl_brw:
                        for get_code2 in get_code.imei_ids:
                            linea_imei = '@'+'Cod/Imei: '+code+'/'+get_code2.imei_code+"\r\n"
                            print linea_imei
                            inv.write(linea_imei)

                    print "Invoice OK" 
                inv.write('010|Gracias por su Compra|'+"\r\n")
                inv.write('101')
                inv.close()
            except IOError as e:
                raise osv.except_osv(_('Error !'), _('Message: %s'%e))
        return arch
        
    def execute_commands(self, cr, uid, ids, context=None):
        inv_brw = self.browse(cr, uid, ids, context)
        for inv in inv_brw:
            if inv.state in ('paid'):
                res = self.fiscal_file_create(cr, uid, ids, context)
                self.ssh_execute(cr, uid, ids, res, context)
                self.write(cr, uid, ids,{'fiscal_voucher':True})
            else:
                self._logger.exception("Exec Cmd: No puede generar una factura fiscal si la factura no esta pagada.")
                raise osv.except_osv(_('Error !'), _('No puede generar una factura fiscal si la factura no esta pagada'))
        return True
        
    def invoice_reverse(self, cr, uid, ids, context=None):
        am_obj = self.pool.get('account.move')
        aml_obj = self.pool.get('account.move.line')
        delete_ids = []
        remove_ids = []
        aml_ids = []
        parent_id = []
        
        aml_ids, parent_id = self.search_concilied_entries(cr, uid, ids, context)
        print "Estos son los aml ", aml_ids
        remove_ids = aml_ids[:]
        remove_ids.append(parent_id[0])
        result = self.remove_move_reconcile(cr, uid, remove_ids, context)
        print "Removimos Conciliaciones ", result
        if result:
            aml_brw = aml_obj.browse(cr, uid, aml_ids, context)
            for reg in aml_brw:
                delete_ids.append(reg.move_id.id)
            print "Estos son los move_ids a borrar ", delete_ids
            am_obj.write(cr, uid, delete_ids, {'state':'draft'})
            self.process_reconcile_credit_note(cr, uid, ids, context)
            am_obj.unlink(cr, uid, delete_ids, context)
        return True
    
    def remove_move_reconcile(self, cr, uid, move_ids=[], context=None):
        # Function remove move rencocile ids related with moves
        obj_move_line = self.pool.get('account.move.line')
        obj_move_rec = self.pool.get('account.move.reconcile')
        unlink_ids = []
        if not move_ids:
            return True
        print "Move Ids remove ", move_ids
        recs = obj_move_line.read(cr, uid, move_ids, ['reconcile_id', 'reconcile_partial_id'])
        full_recs = filter(lambda x: x['reconcile_id'], recs)
        rec_ids = [rec['reconcile_id'][0] for rec in full_recs]
        part_recs = filter(lambda x: x['reconcile_partial_id'], recs)
        part_rec_ids = [rec['reconcile_partial_id'][0] for rec in part_recs]
        unlink_ids += rec_ids
        unlink_ids += part_rec_ids
        if unlink_ids:
            obj_move_rec.unlink(cr, uid, unlink_ids)
        return True
    
    def process_reconcile_credit_note(self, cr, uid, ids, context=None):
        """ Funcion que se encarga de la conciliacion
        automatica de las notas de credito."""
        
        am_obj = self.pool.get("account.move")
        aml_obj = self.pool.get("account.move.line")
        seq_obj = self.pool.get('ir.sequence')
        ai_obj = self.pool.get('account.invoice')
        aj_obj = self.pool.get('account.journal')
        conciliation_ids = []
        child_move_ids = []
        credit_note_amount = 0.00
        
        credit_note_brw = ai_obj.browse(cr, uid, ids, context)
        print "Este es el Browse ", credit_note_brw
        print "Este es el Context ", context
        
        for credit_note in credit_note_brw:
            
            credit_note_amount += credit_note.amount_total
            credit_note_account = credit_note.account_id.id
            credit_note_journal = credit_note.journal_id.id
            credit_note_date = credit_note.date_invoice
            credit_note_date_due = credit_note.date_due
            credit_note_period = credit_note.period_id.id
            credit_note_partner = credit_note.partner_id.id 
            credit_note_name = credit_note.name
            credit_note_reference = credit_note.reference
            
            company_currency = credit_note.journal_id.company_id.currency_id.id
            current_currency = credit_note.currency_id.id
            
            child_move_brw = credit_note.move_id
            child_move_ids.append(credit_note.move_id.id)
            
            for invoice in [credit_note.parent_id]:
                invoice_amount  = invoice.amount_total
                invoice_account = invoice.account_id.id
                parent_move_brw = invoice.move_id
                
        
        print "Esto es el child_move_brw ", child_move_brw
        print "Esto es el parent_move_brw" , parent_move_brw
        print "Monto Total de Notas de Credito ", credit_note_amount
        print "Esto es Child_Move_IDS ", child_move_ids
        
        if (credit_note_amount == invoice_amount):
            #~ Conciliacion Total
            for move_reg in [parent_move_brw]:
                for lines in move_reg.line_id:
                    if lines.account_id.id == credit_note_account and lines.debit > 0.00:
                        conciliation_ids.append(lines.id)
                    if lines.account_id.id == credit_note_account and lines.credit > 0.00:
                            conciliation_ids.append(lines.id)
            for move_reg in [child_move_brw]:
                for lines in move_reg.line_id:
                    if lines.account_id.id == credit_note_account and lines.credit > 0.00:
                            conciliation_ids.append(lines.id)
                    if lines.account_id.id == credit_note_account and lines.debit > 0.00:
                            conciliation_ids.append(lines.id)
            aml_obj.reconcile_partial(cr, uid, conciliation_ids, 'auto', context=context)
        return True
    
    def search_concilied_entries(self, cr, uid, ids, context=None):
        """ Esta Funcion busca los asientos que se han reconciliado con
        la factura"""
        invoice_ids = []
        line_ids = []
        moves_ids = []
        print "Esto es el id ", ids
        nc_brw = self.browse(cr, uid, ids, context)
        for nc in nc_brw:
            invoice_ids.append(nc.parent_id.id)
        if not invoice_ids:
            raise osv.except_osv(_('Error !'), _('No hay una factura asociada a la Nota de credito'))
            
        invoice_brw = self.browse(cr, uid, invoice_ids, context)
        print "Invoice IDS ", invoice_ids
        for invoice in invoice_brw:
            src = []
            lines = []
            if invoice.payment_ids:
                for pay in invoice.payment_ids:
                    line_ids.append(pay.id)
            else:
                raise osv.except_osv(_('Error !'), _('La factura a la que intenta aplicar la nota de credito no esta pagada'))

        print "Resultado ", line_ids
        return line_ids, invoice_ids 
        
    def action_number(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).action_number(cr, uid, ids, context)
        pay = 0.00
        amount = 0.00
        inv_brw = self.browse(cr, uid, ids, context)
        if res:
            for inv in inv_brw:
                if inv.type in ('out_invoice'):
                    amount = inv.amount_total
                    pay = [x.amount for x in inv.account_invoice_payments_lines_ids]
                    pay = sum(pay)
                    if pay != amount:
                         raise osv.except_osv(_('Error !'), _('Message: El Monto de Pago no concuerda con el de la factura'))
                    else:
                        self.payment_lines_move_create(cr, uid, ids, context)
                elif inv.type in ('out_refund'):
                        self.invoice_reverse(cr, uid, ids, context)
        print "Payment ", pay
        return res
    
    def payment_lines_move_create(self, cr, uid, ids, context=None):
        aml_obj = self.pool.get('account.move.line')
        am_obj = self.pool.get('account.move')
        period_obj = self.pool.get('account.period')
        date_move = time.strftime('%Y-%m-%d')
        
        inv_brw = self.browse(cr, uid, ids, context)
        for inv in inv_brw:
            concil_ids = []
            concil_ids.append(aml_obj.search(cr, uid, [('move_id','=',inv.move_id.id),('account_id','=',inv.account_id.id)])[0])
            for payment in inv.account_invoice_payments_lines_ids:
                assent = {
                'name':inv.number,
                'ref':inv.number,
                'journal_id':payment.type_id.journal_id.id,
                'period_id':period_obj.find(cr, uid, date_move, context=context)[0],
                'date':inv.date_invoice,
                'to_check':False,
                }
                val = am_obj.create(cr, uid, assent, context)
                
                l1 = {
                    'ref':inv.number,
                    'invoice':inv.id,
                    'name': 'Pago '+payment.type_id.name,
                    'partner_id': inv.partner_id.id,
                    'account_id': payment.type_id.journal_id.default_debit_account_id.id,
                    'date': inv.date_invoice,
                    'debit': payment.amount,
                    'credit': 0.00,
                    'journal_id':payment.type_id.journal_id.id,
                    'period_id':period_obj.find(cr, uid, date_move, context=context)[0],
                    'currency_id': inv.currency_id.id,
                    'move_id':val,
                }
                print "Esto es l1 ", l1
                l1 = aml_obj.create(cr, uid, l1, context)
                l2 = {
                    'ref':inv.number,
                    'invoice':inv.id,
                    'name': 'Pago '+payment.type_id.name,
                    'partner_id': inv.partner_id.id,
                    'account_id': inv.account_id.id,
                    'date': inv.date_invoice,
                    'debit': 0.00,
                    'credit': payment.amount,
                    'journal_id':payment.type_id.journal_id.id,
                    'period_id':period_obj.find(cr, uid, date_move, context=context)[0],
                    'currency_id': inv.currency_id.id,
                    'move_id':val,
                }
                print "Esto es l2 ", l2
                concil_ids.append(aml_obj.create(cr, uid, l2, context))
                am_obj.button_validate(cr,uid, [val], context)
            print "Ids a Conciliar: ", concil_ids
            aml_obj.reconcile_partial(cr, uid, concil_ids,'auto', context)
        return True
        
account_invoice()

class account_invoice_payment_types(osv.osv):
    _name = "account.invoice.payment.types"
    
    _columns = {
    'name': fields.char('Tipo Pago',size=128,),
    'journal_id': fields.many2one('account.journal','Journal'),
    }
account_invoice_payment_types()

class account_invoice_payment_lines(osv.osv):
    _name = "account.invoice.payment.lines"
    
    _columns = {
    'invoice_id': fields.many2one('account.invoice','Factura'),
    'type_id': fields.many2one('account.invoice.payment.types','Tipo de Pago'),
    'amount':fields.float('Monto'),
    }
account_invoice_payment_lines()
