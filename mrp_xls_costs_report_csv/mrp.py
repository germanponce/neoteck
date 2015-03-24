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

class mrp_bom_indirect_costs(osv.osv):
    _name = 'mrp.bom.indirect.costs'
    _description = 'Costos Indirectos de Lista de Materiales'
    _rec_name = 'product_id' 
    _columns = {
    'bom_id': fields.many2one('mrp.bom','ID Referencia'),
    'product_id': fields.many2one('product.product','Producto', required=True),
    'service_cost': fields.float('Costo', digits=(14,4), required=True),
    }

    def on_change_product_id(self, cr, uid, ids, product_id, context=None):
        product_obj = self.pool.get('product.product')
        res = {}
        if product_id:
            product_br = product_obj.browse(cr, uid, product_id, context=None)
            service_cost = product_br.standard_price
            res.update({'service_cost':service_cost})
        return {'value':res}
mrp_bom_indirect_costs()

class mrp_bom(osv.osv):
    _name = 'mrp.bom'
    _inherit ='mrp.bom'
    _columns = {
        'indirect_costs_ids': fields.one2many('mrp.bom.indirect.costs','bom_id','Gastos Indirectos',
        help='En este campo podemos definir todos aquellos Gastos(Costos) Indirectos para la Produccion de esta Lista de Materiales.', ),
        }

    _defaults = {
        }

mrp_bom()