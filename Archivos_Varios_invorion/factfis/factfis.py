#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

 #* OEOG Envia un archivo a la impresora fiscal
 #*
 #*
 #* @version   Beta 1
 #* @author    Andres Hocevar
 #*
 #* @since     Agosto 10 del 2010
 #**/
 #/***************************************************************************
 #*
 #* Este programa es software libre: usted puede redistribuirlo y / o modificar
 #* bajo los t�rminos de la GNU General Public License publicada por
 #* la Free Software Foundation, bien de la versi�n 3 de la Licencia, o
 #* (A su elecci�n) cualquier versi�n posterior.
 #*
 #* Este programa se distribuye con la esperanza de que sea �til,
 #* pero SIN NINGUNA GARANT�A, incluso sin la garant�a impl�cita de
 #* COMERCIALIZACI�N o IDONEIDAD PARA UN PROP�SITO PARTICULAR. Ver la
 #* Licencia P�blica General GNU para m�s detalles.
 #*
 #* Deber�a haber recibido una copia de la GNU General Public License
 #* junto con este programa. Si no, v�ase <http://www.gnu.org/licenses/>.
 #*
 #***************************************************************************/

import sys
import re
from time import sleep
import fiscales


if len(sys.argv) == 1:
	print "Faltan parametros"
	sys.exit(0)
else:
	arch=sys.argv[1]

try:
	f = open(arch)
except IOError:
	print "El archivo '"+arch+"' no existe"
	sys.exit(0)

fac=False
imp = fiscales.factfis()
imp.mdepura=True
imp.OpenFpctrl()
#lee las lineas
for linea in f:
	if linea and linea[-1] == '\n':
		linea = linea[:-1]
	if linea and linea[-1] == '\r':
		linea = linea[:-1]
	linea=linea.rstrip()
	if len(linea.strip())>0:
		m = re.match(r"i[0-9]{2}[rR][eE][fF][eE][rR][eE][nN][cC][iI][aA][ :]*(?P<numero>[NC0-9]+) *[cC][aA][jJ][aA][ :]*(?P<caja>[0-9]+) *", linea)
		if m!=None:
			referen=m.group('numero')
			caja=m.group('caja')
			fac=True

		if fac and linea=='e':
			print 'En espera para cupones ...'
			#imp.reiniciar()
			sleep(8)
		if imp.SimpleCmd(linea):
			continue
		elif imp.SimpleCmd(linea):
			continue
		elif imp.SimpleCmd(linea):
			continue
		elif imp.SimpleCmd(linea):
			continue
		elif imp.SimpleCmd(linea):
			continue
		else:
			print imp.envio;
f.close()

#para sacar la ultima factura y el serial
if fac:
	m=imp.estado1()
	serial=m[9]
	ufac=m[2];
	f = open("num"+referen+".txt","w")
	f.write('"'+serial+'","'+ufac+'","'+referen+'","'+caja+'"')
	f.close()