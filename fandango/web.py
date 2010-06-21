#!/usr/bin/env python2.5
"""
#############################################################################
##
## file :       web.py
##
## description : see below
##
## project :     Tango Control System
##
## $Author: Sergi Rubio Manrique, srubio@cells.es $
##
## $Revision: 2010 $
##
## copyleft :    ALBA Synchrotron Controls Section, CELLS
##               Bellaterra
##               Spain
##
#############################################################################
##
## This file is part of Tango Control System
##
## Tango Control System is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as published
## by the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## Tango Control System is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
###########################################################################
@package dicts

Some extensions to python dictionary
ThreadDict: Thread safe dictionary with redefinable read/write methods and a backgroud thread for hardware update.
defaultdict_fromkey: Creates a dictionary with a default_factory function that creates new elements using key as argument.
CaselessDict: caseless dictionary
CaselessDefaultDict: a join venture between caseless and default dict

@deprecated
@note see in tau.core.utils.containers

by Sergi Rubio, 
srubio@cells.es, 
2010 
"""
page = lambda s: '<html>%s</html>'%s
body = lambda s: '<body>%s</body>'%s
paragraph = lambda s: '<p>%s</p>'%s
linebreak = '<br>'
separator = '<hr/>'

ulist = lambda s: '<ul>%s</ul>'%s
item = lambda s: '<li>%s</li>'%s

bold = lambda s: '<b>%s</b>'%s
em = lambda s: '<em>'+str(s)+'</em>'

link = lambda s,url: '<a href="%s">%s</a>' % (url,s)
iname = lambda s: s.replace(' ','').lower()
iurl = lambda url: '#'+iname(url)
ilink = lambda s,url: '<a name="%s">%s</a>' % (iname(s),s)
title = lambda s,n=1: '<a name="%s"><h%d>%s</h%d></a>' % (iname(s),n,s,n) #<a> allows to make titles linkable
title1 = lambda s: '<h1>%s</h1>'%s

row,cell = (lambda s: '<tr>%s</tr>'%s) , (lambda s: '<td>%s</td>'%s)
table = lambda s: '<table border=1>'+'\n'.join([row(''.join([cell('%s'%c) for c in r])) for r in s])+'</table>'