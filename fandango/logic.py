#!/usr/bin/env python2.5
"""
#############################################################################
##
## file :       logic.py
##
## description : see below
##
## project :     Tango Control System
##
## $Author: Sergi Rubio Manrique, srubio@cells.es $
##
## $Revision: 2008 $
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
"""

## Some miscellaneous logic methods

def first(seq):
    """Returns first element of sequence"""
    try: 
        return seq[0]
    except Exception,e: 
        try: 
            return seq.next()
        except:
            raise e
    pass

def last(seq):
    """Returns last element of sequence"""
    return seq[-1]

def ormap(seq):
    """Returns first that is true or last that is false"""
    for s in seq:
        if s: return s
    return seq[-1]

def andmap(seq):
    """Returns last that is true or first that is false"""
    for s in seq:
        if not s: return s
    return seq[-1]