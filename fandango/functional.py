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

import operator
import re
from functools import partial
from itertools import count,cycle,repeat,chain,groupby,islice,imap,starmap
from itertools import dropwhile,takewhile,ifilter,ifilterfalse,izip,combinations,permutations,product

__all__ = ['partial','first','last','anyone','everyone','isString','isNumber','isSequence','isDictionary','isIterable']

########################################################################
## Some miscellaneous logic methods
########################################################################
  
def first(seq):
    """Returns first element of sequence"""
    try: 
        return seq[0]
    except Exception,e: 
        try: 
            return seq.next()
        except:
            raise e #if .next() also doesn't work throw unsubscriptable exception
    return

def last(seq,MAX=1000):
    """Returns last element of sequence"""
    try:
        return seq[-1]
    except Exception,e:
        try: 
            n = seq.next()
        except: 
            raise e #if .next() also doesn't work throw unsubscriptable exception
        try:
            for i in range(1,MAX):
                n = seq.next()
            if i>(MAX-1):
                raise IndexError('len(seq)>%d'%MAX)
        except StopIteration,e: #It catches generators end
            return n
    return
        
def xor(A,B):
    """Returns (A and not B) or (not A and B);
    the difference with A^B is that it works also with different types and returns one of the two objects..
    """
    return (A and not B) or (not A and B)

def notNone(arg,default=None):
    """ Returns arg if not None, else returns default. """
    return [arg,default][arg is None]

def join(seqs):
    """ It returns the sum of several sequences as a list """
    result = []
    for seq in seqs:
        result += list(seq)
    return result
    

def anyone(seq,method=bool):
    """Returns first that is true or last that is false"""
    for s in seq:
        if method(s): return s
    return s if not s else None        

def everyone(seq,method=bool):
    """Returns last that is true or first that is false"""
    for s in seq:
        if not method(s): return s if not s else None
    return s
        
########################################################################
## Regular expressions 
########################################################################
        
def matchAll(exprs,seq):
    """ Returns a list of matched strings from sequence.
    If sequence is list it returns exp as a list.
    """
    exprs,seq = toSequence(exprs),toSequence(seq)
    if anyone(isRegexp(e) for e in exprs):
        exprs = [(e.endswith('$') and e or (e+'$')) for e in exprs]
        return [s for s in seq if fun.anyone(re.match(e,s) for e in exprs)]
    else:
        return [s for s in seq if s in exprs]
    
def matchAny(exprs,seq):
    """ Returns seq if any of the expressions in exp is matched, if not it returns None """
    exprs = toSequence(exprs)
    for exp in exprs:
        if matchCl(exp,seq): return seq
    return None
    
def matchMap(mapping,key,regexp=True):
    """ from a mapping type (dict or tuples list) with strings as keys it returns the value from the matched key or raises KeyError exception """
    if not mapping: raise ValueError('mapping')    
    if hasattr(mapping,'items'): mapping = mapping.items()
    if not isSequence(mapping) or not isSequence(mapping[0]): raise TypeError('dict or tuplelist required')
    if not isString(key): key = str(key)
    
    for tag,value in mapping:
        if (matchCl(tag,key) if regexp else (key in tag)):
            return value
    raise KeyError(key)
    
def matchTuples(self,mapping,key,value):
    """ mapping is a (regexp,[regexp]) tuple list where it is verified that value matches any from the matched key """
    for k,regexps in mapping:
        if re.match(k,key):
            if any(re.match(e,value) for e in regexps):
                return True
            else:
                return False
    return True
    
def matchCl(exp,seq):
    """ Returns a caseless match between expression and given string """
    return re.match(exp.lower(),seq.lower())
clmatch = matchCl #For backward compatibility

def searchCl(exp,seq):
    """ Returns a caseless regular expression search between expression and given string """
    return re.search(exp.lower(),seq.lower())
clsearch = searchCl #For backward compatibility

def toRegexp(exp):
    """ Replaces * by .* and ? by . in the given expression. """
    exp = exp.replace('*','.*') if '*' in exp and '.*' not in exp else exp
    exp = exp.replace('?','.') if '?' in exp and not any(s in exp for s in (')?',']?','}?')) else exp
    return exp

########################################################################
## Methods for identifying types        
########################################################################
""" Note of the author:
 This methods are not intended to be universal, are just practical for general Tango application purposes.
"""
        
def isString(seq):
    if isinstance(seq,basestring): return True # It matches most python str-like classes
    return 'string' in str(type(seq)).lower() # It matches QString amongst others
    
def isRegexp(seq):
    RE = r'.^$*+?{[]\|()'
    return anyone(c in RE for c in seq)
    
def isNumber(seq):
    return operator.isNumberType(seq)
    
def isSequence(seq):
    """ It excludes Strings and dictionaries """
    if any(isinstance(seq,t) for t in (list,set,tuple)): return True
    if isString(seq): return False
    if hasattr(seq,'items'): return False
    if hasattr(seq,'__iter__'): return True
    return False
    
def isDictionary(seq):
    """ It includes dicts and also nested lists """
    if isinstance(seq,dict): return True
    if hasattr(seq,'items') or hasattr(seq,'iteritems'): return True
    if seq and isSequence(seq) and isSequence(seq[0]):
        if seq[0] and not isSequence(seq[0][0]): return True #First element of tuple must be hashable
    return False
    
def isIterable(seq):
    """ It includes dicts and listlikes but not strings """
    return hasattr(seq,'__iter__') and not isString(seq)

def str2int(seq):
    """ It returns the first integer encountered in the string """
    return int(re.search('[0-9]+',seq).group())

def str2float(seq):
    """ It returns the first float (x.ye-z) encountered in the string """
    return float(re.search('[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?',seq).group())

def toList(val,default=None,check=isSequence):
    if not val: 
        return default or []
    elif not check(val): #You can use (lambda s:isinstance(s,list)) if you want
        return [val]
    else: 
        return val
    
toSequence = toList