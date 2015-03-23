# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010 german_442
#    All Rights Reserved.
#    info skype: german_442 email: (german.ponce@argil.mx)
############################################################################
#    Coded by: german_442 email: (cherman.seingalt@gmail.com)
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
    'name': 'Reporte de Consumos Costeados en Produccion',
    'version': '1',
    "author" : "German Ponce Dominguez",
    "category" : "Neoteck",
    'description': """

    Este modulo permite Generar un Reporte de Cotos por la Produccion de un Producto, en un Periodo Seleccionado.\n

    Asistente:
    - El Asistente para la Generacion del Reporte se encuenta en el Menu Produccion --> Reportes --> Asistente Reportes de Consumos.

    Historial: \n
    - Tenemos un Historico de Consultas en el Menu Produccion --> Reportes --> Reportes de Consumos.

    Secuencia:
    - El Historico contiene una secuencia que tiene por nombre --> Secuencia Reporte Consumos.
    \nLa cual pueden modificar desde el Menu Configuracion del Sistema.

    Costos Indirectos:
    - Se agrego una pestaña llamada Gastos Indirectos en Lista de materiales, la cual permite añadir Servicios como Gastos Indirectos de Produccion.
    
    \nRequerimientos:\n
    Se necesita la libreria xlsxwriter:
    - sudo pip install xlsxwriter
    """,
    "website" : "http://www.poncesoft.blogspot.mx",
    "license" : "AGPL-3",
    "depends" : ["mrp"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    #'customs_view.xml',
                    'wizard.xml',
                    'mrp_view.xml',
                    'security/ir.model.access.csv',
                    ],
    "installable" : True,
    "active" : False,
}
