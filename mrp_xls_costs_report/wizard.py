# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import pooler
from openerp.addons.decimal_precision import decimal_precision as dp
import time
from openerp import SUPERUSER_ID
from datetime import date, datetime, time, timedelta
import base64
import csv
import StringIO
import os
import hashlib
import tempfile
import xlsxwriter

import sys
reload(sys)  
sys.setdefaultencoding('utf8')

class wizard_consumed_cost_mrp(osv.osv_memory):
    _name = 'wizard.consumed.cost.mrp'
    _description = 'Generacion de Reporte de Consumos'
    _columns = {
    'bom_id': fields.many2one('mrp.bom','Lista Materiales', required=True, ),
    'date_start': fields.date('Fecha Inicio', required=True, ),
    'date_end': fields.date('Fecha Fin', required=True, ),
    }

    def _get_date_start(self, cr, uid, context=None):
        date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        date_strp = datetime.strptime(date_now, '%Y-%m-%d %H:%M:%S')
        year = date_strp.year
        month = date_strp.month
        day = date_strp.day

        date_revision = date_strp - timedelta(days=30)
        return str(date_revision)

       
    _defaults = {
        'date_start': _get_date_start,
        'date_end': lambda *a: datetime.now().strftime('%Y-%m-%d'),
    }


    def get_info(self, cr, uid, ids, context=None):
        self_br = self.browse(cr, uid, ids, context=None)[0]
        mrp_obj = self.pool.get('mrp.production')
        mrp_line_obj = self.pool.get('mrp.production.product.line')
        mrp_ids = mrp_obj.search(cr, uid, [('date_planned','>=', self_br.date_start),
            ('date_planned','<=',self_br.date_end),('state','=','done'),
            ('bom_id','=',self_br.bom_id.id)])
        historical_obj = self.pool.get('historical.consumed.mrp')
        # print "########### MRP IDS >>>>> ", mrp_ids
        if mrp_ids:
            mrp_line_ids = mrp_line_obj.search(cr, uid, [('production_id','in',tuple(mrp_ids))] ,context=None)
            cr.execute("select product_id from mrp_production_product_line where id in %s",(tuple(mrp_line_ids),))
            # print "############ MRP LINES >>> ", mrp_line_ids
            product_ids_cr = cr.fetchall()
            try:
                product_ids = [x[0] for x in product_ids_cr]
            except:
                product_ids = []
            # print "################ PROD IDS >>>> ", product_ids
            if product_ids:
                
                consumed_lines = []
                cost_lines = []
                product_qty = 0.0
                product_amount_total = 0.0
                product_amount_lines = 0.0
                product_cost_lines = 0.0
                for prod in product_ids:
                    total_line = 0.0
                    # print "#####33 prod"
                    prod_br = self.pool.get('product.product').browse(cr, uid, prod, context=None)
                    cr.execute("""select sum (product_qty) from mrp_production_product_line
                        where product_id=%s and id in %s
                        """, (prod,tuple(mrp_line_ids)))
                    try:
                        total_qty_cr = cr.fetchall()[0][0]
                    except:
                        total_qty_cr = 0.0
                    ####### Analizar y sacar un Factor de Conversion de Unidades de Medida #########
                    if total_qty_cr:
                        total_line  = total_qty_cr * prod_br.standard_price
                        product_amount_lines += total_line
                    xline = (0,0,{
                        'name':'[ '+prod_br.default_code+' ]' if prod_br.default_code else '[]',
                        'product_id': prod_br.id,
                        'uom_id': prod_br.uom_id.id,
                        'product_qty': total_qty_cr,
                        'product_cost': prod_br.standard_price,
                        'product_total': total_line, ### Sacar el Factor y hacer el calculo
                        })
                    consumed_lines.append(xline)

                if self_br.bom_id.indirect_costs_ids:
                    cr.execute("select sum (product_qty) from mrp_production where id in %s",(tuple(mrp_ids),))
                    try:
                        mrp_qty = cr.fetchall()[0][0]
                    except:
                        mrp_qty = 0.0
                    for cost_pr in self_br.bom_id.indirect_costs_ids:
                        prod = cost_pr.product_id.id
                        prod_br = self.pool.get('product.product').browse(cr, uid, prod, context=None)

                        factor_cost = cost_pr.service_cost / self_br.bom_id.product_qty
                        cost_total_l = factor_cost * mrp_qty
                        product_cost_lines+= cost_total_l
                        cline = (0,0,{
                            'name': '[ '+prod_br.default_code+' ]' if prod_br.default_code else '[]',
                            'product_id': prod,
                            'product_total': cost_total_l,
                            })
                        cost_lines.append(cline)
            product_amount_total = product_amount_lines + product_cost_lines

            cr.execute("select sum(product_qty) from mrp_production where id in %s",(tuple(mrp_ids),))
            try:
                product_qty = cr.fetchall()[0][0]
            except:
                product_qty = 0.0
            vals = {
                'bom_id': self_br.bom_id.id,
                'product_id': self_br.bom_id.product_tmpl_id.id,
                'uom_id': self_br.bom_id.product_tmpl_id.uom_id.id,
                'product_qty': product_qty,
                'product_amount_total': product_amount_total,
                'product_amount_lines': product_amount_lines,
                'product_cost_lines': product_cost_lines,
                'date_start': self_br.date_start,
                'date_end': self_br.date_end,
                'name':'Producto '+self_br.bom_id.product_tmpl_id.name +' / Consulta de Consumos del pediodo '+self_br.date_start+' - '+self_br.date_end,
                'consumed_lines': [x for x in consumed_lines],
                'cost_lines': [x for x in cost_lines],
            }
        historical_id = historical_obj.create(cr, uid, vals, context=None)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reporte de Consumos MRP'),
            'res_model': 'historical.consumed.mrp',
            'res_id': historical_id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'target': 'current',
            'nodestroy': True,
        }

wizard_consumed_cost_mrp()

class historical_consumed_mrp(osv.osv):
    _name = 'historical.consumed.mrp'
    _description = 'Historico de Consultas de Reportes de Consumos'
    _columns = {
        'bom_id': fields.many2one('mrp.bom','Lista de Materiales', readonly=True, ),
        'product_id': fields.many2one('product.product','Producto', readonly=True, ),
        'uom_id': fields.many2one('product.uom', 'Unidad de Medida', readonly=True, ),
        'product_qty': fields.float('Producto Terminado', digits=(14,2), readonly=True, ),
        'product_amount_total': fields.float('Costo Total', digits=(14,2), readonly=True, ),
        'product_amount_lines': fields.float('Total Consumo Productos', digits=(14,2), readonly=True, ),
        'product_cost_lines': fields.float('Total Gastos Indirectos', digits=(14,2), readonly=True, ),
        'date_start': fields.date('Fecha Inicio', readonly=True, ),
        'date_end': fields.date('Fecha Fin', readonly=True, ),
        'name':fields.char('Descripcion', size=128, readonly=False),
        'sequence' : fields.char('Secuencia', size=128, readonly=True),
        'notes': fields.text('Notas'),
        'consumed_lines': fields.one2many('historical.consumed.product', 'historical_id', 'Productos Consumidos', readonly=True),
        'cost_lines': fields.one2many('historical.consumed.cost', 'historical_id', 'Gastos Indirectos', readonly=True),
    }
    _defaults = {  
        }
    _order = 'id desc' 

    def create(self, cr, uid, vals, context=None):
        sequence = self.pool.get('ir.sequence').get(cr, uid, 'historical.consumed.mrp')
        if sequence:
            vals['sequence'] = sequence
        else:
            return True
        return super(historical_consumed_mrp, self).create(cr, uid, vals, context=context)

    def get_info(self, cr, uid, ids, context=None):
        return True

historical_consumed_mrp()


class historical_consumed_product(osv.osv):
    _name = 'historical.consumed.product'
    _description = 'Productos Consumidos'
    _columns = {
    'name': fields.char('Referencia', size=128),
    'product_id': fields.many2one('product.product', 'Producto'),
    'uom_id': fields.many2one('product.uom', 'Unidad de Medida'),
    'product_qty': fields.float('Cantidad', digits=(12,2)),
    'product_cost': fields.float('Costo', digits=(12,2)),
    'product_total': fields.float('Total', digits=(12,2)),
    'historical_id': fields.many2one('historical.consumed.mrp', 'Ref ID'),


    }
    _defaults = {  
        }
    _order = 'product_id' 

historical_consumed_product()

class historical_consumed_cost(osv.osv):
    _name = 'historical.consumed.cost'
    _description = 'Gastos'
    _columns = {
    'name': fields.char('Referencia', size=128),
    'product_id': fields.many2one('product.product', 'Producto'),
    'product_total': fields.float('Costo Total', digits=(12,2)),
    'historical_id': fields.many2one('historical.consumed.mrp', 'Ref ID'),


    }
    _defaults = {  
        }
    _order = 'product_id' 

historical_consumed_cost()


class agged_xls_export(osv.osv_memory):
    _name = 'agged.xls.export'
    _description = 'Generar Reporte XLS'
    _columns = {
        'datas_fname': fields.char('File Name',size=256),
        'file': fields.binary('Layout'),
        'download_file': fields.boolean('Descargar Archivo'),
        'cadena_decoding': fields.text('Binario sin encoding'),
        'active_ids_str': fields.text('Active IDS'),
    }

    _defaults = {
        'download_file': False,
        }

    def export_xls_file(self, cr, uid, ids, context=None):
        #TODO : OpenERP Business Process 
        document_csv = ""
        datas_fname = ""
        amount_global_total = 0.0
        active_ids = context and context.get('active_ids', False)
        model = context and context.get('active_model', False)
        model_br = self.pool.get(model).browse(cr, uid, active_ids[0])
        for rec in self.browse(cr, uid, ids, context=None):
            ####### GENERACION DEL REPORTE XLSX ########
            # Create an new Excel file and add a worksheet.
            fname=tempfile.NamedTemporaryFile(suffix='.xlsx',delete=False)

            workbook = xlsxwriter.Workbook(fname)
            worksheet = workbook.add_worksheet()

            # Widen the first column to make the text clearer.
            worksheet.set_column('A:K', 20)

            # Add a bold format to use to highlight cells.
            #### ESTILOS DE CELDAS #####
            bold = workbook.add_format({'bold': True})
            format_red = workbook.add_format({'bold': True})

            format_red.set_bg_color('#830000')
            format_red.set_align('center')
            format_red.set_font_color('white')

            format_red_big = workbook.add_format({'bold': True})
            format_red_big.set_bg_color('#830000')
            format_red_big.set_font_size(12)
            format_red_big.set_font_color('white')

            format_black = workbook.add_format({'bold': True})

            format_black.set_bg_color('#000000')
            format_black.set_align('right')
            format_black.set_font_color('white')

            format_gray = workbook.add_format({'bold': True})
            format_gray.set_font_size(12)
            format_gray.set_bg_color('#7A6E6E')

            format_gray_right = workbook.add_format({'bold': True})

            format_gray_right.set_bg_color('#DADEDA')
            format_gray_right.set_align('right')

            # Write some simple text.
            # Cabeceras
            worksheet.write('A1', 'Lista de Materiales', format_red)
            worksheet.write('B1', 'Producto', format_red)
            worksheet.write('C1', 'Unidad de Medida', format_red)
            worksheet.write('D1', 'Cantidad Producto', format_red)
            worksheet.write('E1', 'Costo Total', format_red)

            worksheet.write('A4', 'Productos Consumidos', format_red)

            worksheet.write('A5', 'Referencia', format_gray)
            worksheet.write('B5', 'Producto', format_gray)
            worksheet.write('C5', 'Unidad de Medida', format_gray)
            worksheet.write('D5', 'Cantidad', format_gray)
            worksheet.write('E5', 'Costo', format_gray)
            worksheet.write('F5', 'Total',format_gray)

            cl = len(model_br.consumed_lines)+8
            # print "############# CL", cl

            worksheet.write('A'+str(cl), 'Gastos Indirectos', format_red)

            worksheet.write('A'+str(cl+1), 'Referencia', format_gray)
            worksheet.write('B'+str(cl+1), 'Producto', format_gray)
            worksheet.write('C'+str(cl+1), 'Costo Total', format_gray)

            workbook.close()

            ########### HASTA AQUI SE CERRO Y SE CREO TEMPORALMENTE ########
            #### LO LEEMOS PARA ENCODEARLO A LA BASE ####
            f = open(fname.name, "r")
            data = f.read()
            f.close()
            datas_fname = model_br.sequence+".xlsx"
            rec.write({'cadena_decoding':document_csv,'datas_fname':datas_fname,'file':base64.encodestring(data),'download_file': True})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'agged.xls.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': ids[0],
            'views': [(False, 'form')],
            'target': 'new',
        }