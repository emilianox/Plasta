#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Informática MEG <contacto@informaticameg.com>
#
# Written by 
#       Copyright 2012 Fernandez, Emiliano <emilianohfernandez@gmail.com>
#       Copyright 2012 Ferreyra, Jonathan <jalejandroferreyra@gmail.com>
#
# Plasta is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 2.1 of
# the License, or (at your option) any later version.
#
# Plasta is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from storm.locals import * #@UnusedWildImport
import storm
from plasta.logic.inspection import Inspection
from storm.exceptions import OperationalError


class BaseManager( object , Inspection):
    '''
    Clase base para manager de una clase storm
    @param seachname: atributo por el cual buscara el metodo get()
    @param reset: si es true limpia y crea la bd  
    '''
    
    def __init__( self, almacen, reset = False ):
        ''''''
        #@param CLASS: la clase que va a manipular ej:Cliente
        self.CLASS = None 
        #@param searchname: lacolumna por la cual el metodo get hace la busqueda ej=Cliente.nombres
        self.searchname = None 
      
        #@param almacen: el objeto STORE de storm 
        self.almacen = almacen
        #@param reset: variable que determina si se va a resetear 
        self.reset = reset
                
        Inspection.__init__(self, self.CLASS )
        
    def _start_operations( self ):
        '''
        operaciones que se requieren para iniciar el manager
        '''
        if self.reset:
            self._reset()        
        print "Manager de %s levantado correctamente" % self.CLASS
        #@param CLASSid: la clave primaria de la clase ej:"ide"        
        self.CLASSid = self.getClassIdString()
        
#=======================================================================
# Methods exclusive Plasta 
#=======================================================================
        

    def _reset( self ):
        '''
        borra y vuelve a crear la tabla 
        '''
        SQL = self._getTableSql()
        nombredetabla = self.CLASS.__storm_table__
        #ELIMINO LA TABLA
        try:
            self.almacen.execute( 'DROP TABLE ' + nombredetabla )
        except OperationalError, e:
            print e
        #CREO NUEVAMENTE LA TABLA
        self.almacen.execute( 'CREATE TABLE ' + nombredetabla + ' ' + SQL )
        self.almacen.commit()

    def getClassName( self ):
        '''
        devuelve el nombre de la clase que maneja
        @return: str
        '''
        return self.CLASS.__name__
 
    def getDataObject( self, obj, columns ):
        '''
        obtiene y devuelve una lista de los datos obtenidos a partir de las
        columnas y de los datos que maneja
        @param obj:objeto instancia a extrer ex:unCliente
        @param columns:storm columns :ex:[Cliente.ide,Cliente.nombres]
        @return: lista de dic: [{"ide":1},{"nombres":nombrecliente}]
        '''
        if isinstance( obj, self.CLASS ):
            listpropiertisvalues = []
            for propiedad in columns:
                nombreatributo = self.getAttributeName( propiedad )
                listpropiertisvalues.append( {nombreatributo:obj.__getattribute__( nombreatributo )} )
            return listpropiertisvalues
        else:
            raise Exception( "No se pudo obtener los valores debido a que no es una instancia correcta" )
     
    def getClassAttributesValues( self, obj ):
        '''
        obtiene los valores de el obj
        @param obj:a obj de type 
        @return: a list of values
        '''
        if isinstance( obj, self.CLASS ):
            return [obj.__getattribute__( p ) for p in self.getClassAttributes()]
        else:
            raise Exception( "no se pudo obtener los valores" )
        
#=======================================================================
# Generic Methods  
#=======================================================================

    def add( self, *params ):
        '''
        Crea y agrega un objeto al almacen
        @param *params: los parametros que recibe el init de self.CLASS
        @return: true o false, dependiendo si se completo la operacion
        '''
        try:
            obj = self.CLASS( *params )
            self.almacen.add( obj )
            self.almacen.flush()
            self.almacen.commit()
            return True
        except Exception, e:
            print e
            return False
        
    def delete( self, obj ):
        '''
        borra un objeto de la bd y de la ram
        @param obj:un objeto del tipo self.CLASS
        '''
        if isinstance( obj, self.CLASS ):
            self.almacen.remove( obj )#where o is the object representing the row you want to remove
            del obj#lo sacamos de la ram
            self.almacen.commit()
            return True
        return False
        
    def getall( self ):
        '''
        obtiene todos los objetos de este manager
        @return: lista de objs
        '''
        return [obj for obj in self.almacen.find( self.CLASS )]

    def get( self, nombre ):
        '''
        obtiene los objetos donde "nombre" coincide con self.searchname
        @param nombre:str o int
        @return: list of obj
        '''
        if not self.searchname:
            self.searchname = self.CLASS.nombre
        return self.searchBy( self.searchname, nombre )

    def searchBy( self, column, nombre ):
        '''
        hace una busqueda e el atributo column por el valor nombre
        @param column:a storm column
        @param nombre:str o int
        @return: lista de objetos
        '''
        if type( column ) == storm.references.Reference:
            objs = self.getall()
            name = self._getReferenceName( column )
            return [obj for obj in objs if nombre in obj.__getattribute__( name ).__str__()]
        if nombre != "":
            import datetime
            if (type( nombre ) is unicode) or (type( nombre ) is str):
                return [obj for obj in self.almacen.find( self.CLASS, column.like( unicode( u"%" + nombre + u"%" ) ) )]
            elif type( nombre ) is int :
                return [obj for obj in self.almacen.find( self.CLASS, column == nombre )]
            elif ( type( nombre ) is datetime.datetime ) or ( type( nombre ) is datetime.date ):
                return [obj for obj in self.almacen.find( self.CLASS, column == nombre )]
            else:
                raise Exception, u"Exception:No se busco adecuadamente debido a que el tipo de criterio es: " + unicode( type( nombre ) )
        else:
            return self.getall()
