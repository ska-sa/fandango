#!/usr/bin/env python2.5
""" @if gnuheader
#############################################################################
##
## file :       device.py
##
## description : CLASS FOR Enhanced TANGO DEVICE SERVERs
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
@endif
@package tango
@brief provides tango utilities for fandango, like database search methods and emulated Attribute Event/Value types
@todo @warning IMPORTING THIS MODULE IS CAUSING SOME ERRORS WHEN CLOSING PYTHON DEVICE SERVERS,  BE CAREFUL!

This module is a light-weight set of utilities for PyTango.
Classes dedicated for device management will go to fandango.device
Methods for Astor-like management will go to fandango.servers
"""

#python imports
import time,re,os

#pytango imports
import PyTango
from PyTango import AttrQuality
if 'Device_4Impl' not in dir(PyTango):
    PyTango.Device_4Impl = PyTango.Device_3Impl

#taurus imports, here USE_TAU is defined for all fandango
try:
    assert str(os.getenv('USE_TAU')).strip().lower() not in 'no,false,0'
    import taurus
    TAU = taurus
    USE_TAU=True
    """USE_TAU will be used to choose between taurus.Device and PyTango.DeviceProxy"""
except:
    print 'fandango.tango: USE_TAU disabled'
    USE_TAU=False

import objects
import functional as fun
from dicts import CaselessDefaultDict,CaselessDict
from objects import Object,Struct
from log import Logger

####################################################################################################################
##@name Access Tango Devices and Database

##TangoDatabase singletone, This object is not thread safe, use TAU database if possible
global TangoDatabase,TangoDevice
TangoDatabase,TangoDevice = None,None

def get_database(): 
    global TangoDatabase
    if TangoDatabase is None:
        try: 
            TangoDatabase = USE_TAU and taurus.Database() or PyTango.Database()
        except: pass
    return TangoDatabase

def get_device(dev): 
    if isinstance(dev,basestring): 
        if USE_TAU: return TAU.Device(dev)
        else: return PyTango.DeviceProxy(dev)
    elif isinstance(dev,PyTango.DeviceProxy) or (USE_TAU and isinstance(dev,TAU.core.tango.TangoDevice)):
        return dev
    else:
        return None

def get_database_device(): 
    global TangoDevice
    if TangoDevice is None:
        try:
           TangoDevice = get_device(TangoDatabase.dev_name())
        except: pass
    return TangoDevice

try:
    #TangoDatabase = USE_TAU and taurus.core.TaurusManager().getFactory()().getDatabase() or PyTango.Database()
    TangoDatabase = get_database()
    TangoDevice = get_database_device()
except: pass
    
def add_new_device(server,klass,device):
    dev_info = PyTango.DbDevInfo()
    dev_info.name = device
    dev_info.klass = klass
    dev_info.server = server
    get_database().add_device(dev_info)    
    
def parse_db_command_array(data,keys=1,depth=2):
    """ 
    This command will parse data received from DbGetDeviceAttributeProperty2 command.
    DB device commands return data in this format: X XSize Y YSize Z ZSize ZValue W WSize WValue
    This corresponds to {X:{Y:{Z:[Zdata],W:[Wdata]}}}
    Depth of the array is 2 by default
    e.g.: 
    label_of_dev_test_attribute = parse_db_command_array(dbd.DbGetDeviceAttributeProperty2([dev,attr]).,keys=1,depth=2)[dev][attr]['label'][0]
    """
    dict = {}
    #print '[%s]: %s' % (keys,data)
    for x in range(keys):
        key = data.pop(0)
        try: length = data.pop(0)
        except: None
        #print '%s,%s,%s => '%(key,length,depth)
        if depth:
            k,v = key,parse_db_command_array(data,keys=int(length),depth=depth-1)
        else:
            try:
                length = int(length)
                k,v = key,[data.pop(0) for y in range(length)]
            except:
                k,v = key,[length]
        #print '\t%s,%s'%(k,v)
        dict.update([(k,v)])
    return dict

def get_attribute_label(target,use_db=True):
    dev,attr = target.rsplit('/',1)
    if not use_db: #using AttributeProxy
        if attr.lower() in ('state','status'): 
            return attr
        ap = PyTango.AttributeProxy(target)
        cf = ap.get_config()
        return cf.label
    else: #using DatabaseDevice
        return (get_database().get_device_attribute_property(dev,[attr])[attr].get('label',[attr]) or [''])[0]
    
def set_attribute_label(target,label='',unit=''):
    if target.lower().rsplit('/')[-1] in ('state','status'): 
        return
    ap = PyTango.AttributeProxy(target)
    cf = ap.get_config()
    if label: cf.label = label
    if unit: cf.unit = unit
    ap.set_config(cf)

def get_device_started(target):
    """ Returns device started time """
    return get_database_device().DbGetDeviceInfo(target)[-1][5]
        
def get_devices_properties(expr,properties,hosts=[],port=10000):
    """get_devices_properties('*alarms*',props,hosts=[get_bl_host(i) for i in bls])"""
    if not isinstance(properties,dict): properties = dict.fromkeys(properties,[])
    get_devs = lambda db, reg : [d for d in db.get_device_name('*','*') if not d.startswith('dserver') and fandango.matchCl(reg,d)]
    if hosts: tango_dbs = dict(('%s:%s'%(h,port),PyTango.Database(h,port)) for h in hosts)
    else: tango_dbs = {os.getenv('TANGO_HOST'):PyTango.Database()}
    return dict(('/'.join((host,d)),db.get_device_property(d,properties.keys())) for host,db in tango_dbs.items() for d in get_devs(db,expr))
    
def get_device_for_alias(alias):
    try: return get_database().get_device_alias(alias)
    except Exception,e:
        if 'no device found' in str(e).lower(): return None
        return None #raise e

def get_alias_for_device(dev):
    try: return get_database().get_alias(dev) #.get_database_device().DbGetDeviceAlias(dev)
    except Exception,e:
        if 'no alias found' in str(e).lower(): return None
        return None #raise e

def get_alias_dict(exp='*'):
    tango = get_database()
    return dict((k,tango.get_device_alias(k)) for k in tango.get_device_alias_list(exp))

def get_real_name(dev,attr=None):
    """
    It translate any device/attribute string by name/alias/label
    """
    if fandango.isString(dev):
        if attr is None and dev.count('/') in (1,4 if ':' in dev else 3): dev,attr = dev.rsplit('/',1)
        if '/' not in dev: dev = get_device_for_alias(dev)
        if attr is None: return dev
    for a in get_device_attributes(dev):
        if fandango.matchCl(attr,a): return (dev+'/'+a)
        if fandango.matchCl(attr,get_attribute_label(dev+'/'+a)): return (dev+'/'+a)
    return None

def get_device_commands(dev):
    return [c.cmd_name for c in get_device(dev).command_list_query()]

def get_device_attributes(dev,expressions='*'):
    """ Given a device name it returns the attributes matching any of the given expressions """
    expressions = map(fun.toRegexp,fun.toList(expressions))
    al = (get_device(dev) if fandango.isString(dev) else dev).get_attribute_list()
    result = [a for a in al for expr in expressions if fun.matchCl(expr,a,terminate=True)]
    return result
        
def get_device_labels(target,filters='',brief=True):
    """
    Returns an {attr:label} dict for all attributes of this device 
    Filters will be a regular expression to apply to attr or label.
    If brief is True (default) only those attributes with label are returned.
    This method works offline, does not need device to be running
    """
    labels = {}
    if fandango.isString(target): d = get_device(target)
    else: d,target = target,target.name()
    db = get_database()
    attrlist = db.get_device_attribute_list(target,filters) if brief else d.get_attribute_list()
    for a in attrlist:
        l = get_attribute_label(target+'/'+a,use_db=True) if brief else d.get_attribute_config(a).label
        if (not filters or any(map(fun.matchCl,(filters,filters),(a,l)))) and (not brief or l!=a): 
            labels[a] = l
    return labels

def get_matching_device_attribute_labels(device,attribute):
    """ To get all gauge port labels: get_matching_device_attribute_labels('*vgct*','p*') """
    devs = get_matching_devices(device)
    return dict((t+'/'+a,l) for t in devs for a,l in get_device_labels(t,attribute).items())

def set_device_labels(target,labels):
    """
    Applies an {attr:label} dict for attributes of this device 
    """
    labels = CaselessDict(labels)
    d = get_device(target)
    for a in d.get_attribute_list():
        if a in labels:
            ac = d.get_attribute_config(a)
            ac.label = labels[a]
            d.set_attribute_config(ac)
    return labels
    
def property_undo(dev,prop,epoch):
    db = get_database()
    his = db.get_device_property_history(dev,prop)
    valids = [h for h in his if fun.str2time(h.get_date())<epoch]
    news = [h for h in his if fun.str2time(h.get_date())>epoch]
    if valids and news:
        print('Restoring property %s/%s to %s'%(dev,prop,valids[-1].get_date()))
        db.put_device_property(dev,{prop:valids[-1].get_value().value_string})
    elif not valids:print('No property values found for %s/%s before %s'%(dev,prop,fun.time2str(epoch)))
    elif not news: print('Property %s/%s not modified after %s'%(dev,prop,fun.time2str(epoch)))
    
def get_matching_device_properties(dev,prop,exclude=''):
    db = get_database()
    result = {}
    devs = dev if fun.isSequence(dev) else get_matching_devices(dev) #devs if fun.isSequence(dev) else [devs]
    props = prop if fun.isSequence(prop) else list(set(s for d in devs for s in db.get_device_property_list(d,prop)))
    print 'devs: %s'%devs
    print 'props: %s'%props
    for d in devs:
        if exclude and fun.matchCl(exclude,d): continue
        r = {}
        vals = db.get_device_property(d,props)
        for k,v in vals.items():
            if v: r[k] = v[0]
        if r: result[d] = r
    if not fun.isSequence(devs) or len(devs)==1:
        if len(props)==1: return result.values()[0].values()[0]
        else: return result.values()[0]
    else: return result

####################################################################################################################
##@name Methods for searching the database with regular expressions
#@{

#Regular Expressions
metachars = re.compile('([.][*])|([.][^*])|([$^+\-?{}\[\]|()])')
#alnum = '[a-zA-Z_\*][a-zA-Z0-9-_\*]*' #[a-zA-Z0-9-_]+ #Added wildcards
alnum = '(?:[a-zA-Z0-9-_\*]|(?:\.\*))(?:[a-zA-Z0-9-_\*]|(?:\.\*))*'
no_alnum = '[^a-zA-Z0-9-_]'
no_quotes = '(?:^|$|[^\'"a-zA-Z0-9_\./])'
rehost = '(?:(?P<host>'+alnum+'(?:\.'+alnum+')?'+'(?:\.'+alnum+')?'+':[0-9]+)(?:/))' #(?:'+alnum+':[0-9]+/)?
redev = '(?P<device>'+'(?:'+'/'.join([alnum]*3)+'))' #It matches a device name
reattr = '(?:/(?P<attribute>'+alnum+')(?:(?:\\.)(?P<what>quality|time|value|exception))?)' #Matches attribute and extension
retango = '(?:tango://)?'+(rehost+'?')+redev+(reattr+'?')+'(?:\$?)' 

def parse_labels(text):
    if any(text.startswith(c[0]) and text.endswith(c[1]) for c in [('{','}'),('(',')'),('[',']')]):
        try:
            labels = eval(text)
            return labels
        except Exception,e:
            print 'ERROR! Unable to parse labels property: %s'%str(e)
            return []
    else:
        exprs = text.split(',')
        if all(':' in ex for ex in exprs):
            labels = [tuple(e.split(':',1)) for e in exprs]
        else:
            labels = [(e,e) for e in exprs]  
        return labels
        
def parse_tango_model(name):
    """
    {'attributename': 'state',
    'devicename': 'bo01/vc/ipct-01',
    'host': 'alba02',
    'port': '10000',
    'scheme': 'tango'}
    """
    values = {'scheme':'tango'}
    values['host'],values['port'] = os.getenv('TANGO_HOST').split(':',1)
    try:
        if not USE_TAU: raise Exception('NotTau')
        from taurus.core import tango as tctango
        from taurus.core import AttributeNameValidator,DeviceNameValidator
        validator = {tctango.TangoDevice:DeviceNameValidator,tctango.TangoAttribute:AttributeNameValidator}
        values.update((k,v) for k,v in validator[tctango.TangoFactory().findObjectClass(name)]().getParams(name).items() if v)
    except:
        name = str(name).replace('tango://','')
        m = re.match(fandango.tango.retango,name)
        if m:
            gd = m.groupdict()
            values['devicename'] = '/'.join([s for s in gd['device'].split('/') if ':' not in s])
            if gd.get('attribute'): values['attributename'] = gd['attribute']
            if gd.get('host'): values['host'],values['port'] = gd['host'].split(':',1)
    return values if 'devicename' in values else None

import fandango.objects
class get_all_devices(fandango.objects.SingletonMap):
    def __init__(self,exported=False,keeptime=60):
        self._all_devs = []
        self._last_call = 0
        self._keeptime = keeptime #Only 1 query/minute to DB allowed
        self._exported = exported
    def get_all_devs(self):
        now = time.time()
        if not self._all_devs or now>(self._last_call+self._keeptime):
            print 'updating all_devs ...'
            self._all_devs = list(get_database().get_device_exported('*') if self._exported else get_database().get_device_name('*','*'))
            self._last_call = now
        return self._all_devs
    def __new__(cls,*p,**k):
        instance = fandango.objects.SingletonMap.__new__(cls,*p,**k)
        return instance.get_all_devs()
    
def get_matching_devices(expressions,limit=0,exported=False):
    """ 
    Searches for devices matching expressions, if exported is True only running devices are returned 
    """
    if not fun.isSequence(expressions): expressions = [expressions]
    all_devs = []
    if any(not fun.matchCl(rehost,expr) for expr in expressions): all_devs.extend(get_all_devices(exported))
    for expr in expressions:
        m = fun.matchCl(rehost,expr) 
        if m:
            host = m.groups()[0]
            print 'get_matching_devices(%s): getting %s devices ...'%(expr,host)
            odb = PyTango.Database(*host.split(':'))
            all_devs.extend('%s/%s'%(host,d) for d in odb.get_device_name('*','*'))
    expressions = map(fun.toRegexp,fun.toList(expressions))
    result = filter(lambda d: any(fun.matchCl(e,d,terminate=True) for e in expressions),all_devs)
    return result[:limit] if limit else result
        
find_devices = get_matching_devices
    
def get_matching_attributes(expressions,limit=0):
    """ 
    Returns all matching device/attribute pairs. 
    regexp only allowed in attribute names
    :param expressions: a list of expressions like [domain_wild/family_wild/member_wild/attribute_regexp] 
    """
    attrs = []
    def_host = os.getenv('TANGO_HOST')
    if not fun.isSequence(expressions): expressions = [expressions]
    #expressions = map(fun.partial(fun.toRegexp,terminate=True),fun.toList(expressions))
    for e in expressions:
        match = fun.matchCl(retango,e,terminate=True)
        if not match:
            if '/' not in e:
                host,dev,attr = def_host,e.rsplit('/',1)[0],'state'
                #raise Exception('Expression must match domain/family/member/attribute shape!: %s'%e)
            else:
                host,dev,attr = def_host,e.rsplit('/',1)[0],e.rsplit('/',1)[1]
        else:
            host,dev,attr = [d[k] for k in ('host','device','attribute') for d in (match.groupdict(),)]
            host,attr = host or def_host,attr or 'state'
        #print '%s => %s: %s /%s' % (e,host,dev,attr)
        for d in get_matching_devices(dev,exported=True):
            if fun.matchCl(attr,'state',terminate=True):
                attrs.append(d+'/State')
            if attr.lower().strip() != 'state':
                try: 
                    ats = get_device_attributes(d,[attr])
                    attrs.extend([d+'/'+a for a in ats])
                    if limit and len(attrs)>limit: break
                except: 
                    print 'Unable to get attributes for %s'%d
    result = list(set(attrs))
    return result[:limit] if limit else result
                    
find_attributes = get_matching_attributes
    
def get_all_models(expressions,limit=1000):
    ''' 
    Customization of get_matching_attributes to be usable in Taurus widgets.
    It returns all the available Tango attributes (exported!) matching any of a list of regular expressions.
    '''
    if isinstance(expressions,str): #evaluating expressions ....
        if any(re.match(s,expressions) for s in ('\{.*\}','\(.*\)','\[.*\]')): expressions = list(eval(expressions))
        else: expressions = expressions.split(',')
    elif isinstance(expressions,(USE_TAU and QtCore.QStringList or list,list,tuple,dict)):
        expressions = list(str(e) for e in expressions)
        
    print 'In get_all_models(%s:"%s") ...' % (type(expressions),expressions)
    db = get_database()
    if 'SimulationDatabase' in str(type(db)): #used by TauWidgets displayable in QtDesigner
      return expressions
    return get_matching_attributes(expressions,limit)
              
#@}
########################################################################################    

########################################################################################
## Methods for managing device/attribute lists    
    
def attr2str(attr_value):
    att_name = '%s='%attr_value.name if hasattr(attr_value,'name') else ''
    if hasattr(attr_value,'value'):
        return '%s%s(%s)' %(att_name,type(attr_value.value).__name__,attr_value.value)
    else: 
        return '%s%s(%s)' %(att_name,type(attr_value).__name__,attr_value)
            
def get_distinct_devices(attrs):
    """ It returns a list with the distinct device names appearing in a list """
    return sorted(list(set(a.rsplit('/',1)[0] for a in attrs)))            
            
def get_distinct_domains(attrs):
    """ It returns a list with the distinc member names appearing in a list """
    return sorted(list(set(a.split('/')[0].split('-')[0] for a in attrs)))            

def get_distinct_families(attrs):
    """ It returns a list with the distinc member names appearing in a list """
    return sorted(list(set(a.split('/')[1].split('-')[0] for a in attrs)))            

def get_distinct_members(attrs):
    """ It returns a list with the distinc member names appearing in a list """
    return sorted(list(set(a.split('/')[2].split('-')[0] for a in attrs)))            

def get_distinct_attributes(attrs):
    """ It returns a list with the distinc attribute names (excluding device) appearing in a list """
    return sorted(list(set(a.rsplit('/',1)[-1] for a in attrs)))

def reduce_distinct(group1,group2):
    """ It returns a list of (device,domain,family,member,attribute) keys that appear in group1 and not in group2 """
    vals,rates = {},{}
    try:
        target = 'devices'
        k1,k2 = get_distinct_devices(group1),get_distinct_devices(group2)
        vals[target] = [k for k in k1 if k not in k2]
        rates[target] = float(len(vals[target]))/(len(k1))
    except: vals[target],rates[target] = [],0
    try:
        target = 'domains'
        k1,k2 = get_distinct_domains(group1),get_distinct_domains(group2)
        vals[target] = [k for k in k1 if k not in k2]
        rates[target] = float(len(vals[target]))/(len(k1))
    except: vals[target],rates[target] = [],0
    try:
        target = 'families'
        k1,k2 = get_distinct_families(group1),get_distinct_families(group2)
        vals[target] = [k for k in k1 if k not in k2]
        rates[target] = float(len(vals[target]))/(len(k1))
    except: vals[target],rates[target] = [],0
    try:
        target = 'members'
        k1,k2 = get_distinct_members(group1),get_distinct_members(group2)
        vals[target] = [k for k in k1 if k not in k2]
        rates[target] = float(len(vals[target]))/(len(k1))
    except: vals[target],rates[target] = [],0
    try:
        target = 'attributes'
        k1,k2 = get_distinct_attributes(group1),get_distinct_attributes(group2)
        vals[target] = [k for k in k1 if k not in k2]
        rates[target] = float(len(vals[target]))/(len(k1))
    except: vals[target],rates[target] = [],0
    return first((vals[k],rates[k]) for k,r in rates.items() if r == max(rates.values()))
 

########################################################################################
            
########################################################################################
## Methods for checking device/attribute availability
            
def get_db_device():
    return TangoDevice

def get_device_info(dev):
    """
    This method provides an alternative to DeviceProxy.info() for those devices that are not running
    """
    #vals = PyTango.DeviceProxy('sys/database/2').DbGetDeviceInfo(dev)
    vals = TangoDevice.DbGetDeviceInfo(dev)
    di = Struct([(k,v) for k,v in zip(('name','ior','level','server','host','started','stopped'),vals[1])])
    di.exported,di.PID = vals[0]
    return di

def get_device_host(dev):
    """
    Asks the Database device server about the host of this device 
    """
    return get_device_info(dev).host

def get_polled_attrs(device,others=None):
    """ 
    @TODO: Tango8 has its own get_polled_attr method; check for incompatibilities
    if a device is passed, it returns the polled_attr property as a dictionary
    if a list of values is passed, it converts to dictionary
    others argument allows to get extra property values in a single DB call 
    """
    if fun.isSequence(device):
        return dict(zip(map(str.lower,device[::2]),map(float,device[1::2])))
    elif isinstance(device,PyTango.DeviceProxy):
        attrs = device.get_attribute_list()
        periods = [(a.lower(),int(dp.get_attribute_poll_period(a))) for a in attrs]
        return dict((a,p) for a,p in periods if p)
    else:
        others = others or []
        if isinstance(device,PyTango.DeviceImpl):
            db = PyTango.Util.instance().get_database()
            #polled_attrs = {}
            #for st in self.get_admin_device().DevPollStatus(device.get_name()):
                #lines = st.split('\n')
                #try: polled_attrs[lines[0].split()[-1]]=lines[1].split()[-1]
                #except: pass
            #return polled_attrs
            device = device.get_name()
        else:
            db = fandango.get_database()
        props = db.get_device_property(device,['polled_attr']+others)
        d = get_polled_attrs(props.pop('polled_attr'))
        if others: d.update(props)
        return d
   
def check_host(host):
    """
    Pings a hostname, returns False if unreachable
    """
    import fandango.linos
    print 'Checking host %s'%host
    return fandango.linos.ping(host)[host]

def check_starter(host):
    """
    Checks host's Starter server
    """
    if check_host(host):
        return check_device('tango/admin/%s'%(host.split('.')[0]))
    else:
        return False
    
def check_device(dev,attribute=None,command=None,full=False):
    """ 
    Command may be 'StateDetailed' for testing HdbArchivers 
    It will return True for devices ok, False for devices not running and None for unresponsive devices.
    """
    try:
        if full:
            info = get_device_info(dev)
            if not info.exported:
                return False
            if not check_host(info.host):
                return False
            if not check_device('dserver/%s'%info.server,full=False):
                return False
        dp = PyTango.DeviceProxy(dev)
        dp.ping()
    except:
        return False
    try:
        if attribute: dp.read_attribute(attribute)
        elif command: dp.command_inout(command)
        else: dp.state()
        return True
    except:
        return None            

def check_attribute(attr,readable=False,timeout=0):
    """ checks if attribute is available.
    :param readable: Whether if it's mandatory that the attribute returns a value or if it must simply exist.
    :param timeout: Checks if the attribute value have been effectively updated (check zombie processes).
    """
    try:
        #PyTango.AttributeProxy(attr).read()
        dev,att = attr.lower().rsplit('/',1)
        assert att in [str(s).lower() for s in PyTango.DeviceProxy(dev).get_attribute_list()]
        try: 
            attvalue = PyTango.AttributeProxy(attr).read()
            if readable and attvalue.quality == PyTango.AttrQuality.ATTR_INVALID:
                return None
            elif timeout and attvalue.time.totime()<(time.time()-timeout):
                return None
            else:
                return attvalue
        except Exception,e: 
            return None if readable else e
    except:
        return None    

def check_device_list(devices,attribute=None,command=None):
    """ 
    This method will check a list of devices grouping them by host and server; minimizing the amount of pings to do.
    """
    result = {}
    from collections import defaultdict
    hosts = defaultdict(lambda:defaultdict(list))
    for dev in devices:
        info = get_device_info(dev)
        if info.exported:
            hosts[info.host][info.server].append(dev)
        else:
            result[dev] = False
    for host,servs in hosts.items():
        if not check_host(host):
            print 'Host %s failed, discarding %d devices'%(host,sum(len(s) for s in servs.values()))
            result.update((d,False) for s in servs.values() for d in s)
        else:
            for server,devs in servs.items():
                if not check_device('dserver/%s'%server,full=False):
                    print 'Server %s failed, discarding %d devices'%(server,len(devs))
                    result.update((d,False) for d in devs)
                else:
                    for d in devs:
                        result[d] = check_device(d,attribute=attribute,command=command,full=False)
    return result
                    
                    
########################################################################################
## A useful fake attribute value and event class

def cast_tango_type(value_type):
    """ Returns the python equivalent to a Tango type"""
    if value_type in (PyTango.DevBoolean,): 
        return bool
    elif value_type in (PyTango.DevDouble,PyTango.DevFloat): 
        return float
    elif value_type in (PyTango.DevState,PyTango.DevShort,PyTango.DevInt,PyTango.DevLong,PyTango.DevLong64,PyTango.DevULong,PyTango.DevULong64,PyTango.DevUShort,PyTango.DevUChar): 
        return int
    else: 
        return str

class fakeAttributeValue(object):
    """ This class simulates a modifiable AttributeValue object (not available in PyTango)
    :param parent: Apart of common Attribute arguments, parent will be used to keep a proxy to the parent object (a DeviceProxy or DeviceImpl) 
    """
    def __init__(self,name,value=None,time_=0.,quality=PyTango.AttrQuality.ATTR_VALID,dim_x=1,dim_y=1,parent=None,device=''):
        self.name=name
        self.device=device or (self.name.split('/')[-1] if '/' in self.name else '')
        self.value=value
        self.write_value = None
        self.time=time_ or time.time()
        self.quality=quality
        self.dim_x=dim_x
        self.dim_y=dim_y
        self.parent=parent
        
    def get_name(self): return self.name
    def get_value(self): return self.value
    def get_date(self): return self.date
    def get_quality(self): return self.quality
    
    def set_value(self,value,dim_x=1,dim_y=1):
        self.value = value
        self.dim_x = dim_x
        self.dim_y = dim_y
        #if fun.isSequence(value):
            #self.dim_x = len(value)
            #if value and fun.isSequence(value[0]):
                #self.dim_y = len(value[0])
        self.set_date(time.time())
    def set_date(self,timestamp):
        if not isinstance(timestamp,PyTango.TimeVal): 
            timestamp=PyTango.TimeVal(timestamp)
        self.time=timestamp
    def set_quality(self,quality):
        self.quality=quality
        
    def set_value_date(self,value,date):
        self.set_value(value)
        self.set_date(date)
    def set_value_date_quality(self,value,date,quality):
        self.set_value_date(value,date)
        self.set_quality(quality)
        
    def set_write_value(self,value):
        self.write_value = value
    def get_write_value(self,data = None):
        if data is None: data = []
        if fun.isSequence(self.write_value):
            [data.append(v) for v in self.write_value]
        else:
            data.append(self.write_value)
        return data
        
from dicts import Enumeration
fakeEventType = Enumeration(
    'fakeEventType', (
        'Change',
        'Config',
        'Periodic',
        'Error'
    ))
    
class fakeEvent(object):
    def __init__(self,device,attr_name,attr_value,err,errors):
        self.device=device
        self.attr_name=attr_name
        self.attr_value=attr_value
        self.err=err
        self.errors=errors
        
####################################################################################################################
## The ProxiesDict class, to manage DeviceProxy pools

class ProxiesDict(CaselessDefaultDict,Object): #class ProxiesDict(dict,log.Logger):
    ''' Dictionary that stores PyTango.DeviceProxies
    It is like a normal dictionary but creates a new proxy each time that the "get" method is called
    An earlier version is used in PyTangoArchiving.utils module
    This class must be substituted by Tau.Core.TauManager().getFactory()()
    '''
    def __init__(self):
        self.log = Logger('ProxiesDict')
        self.log.setLogLevel('INFO')
        self.call__init__(CaselessDefaultDict,self.__default_factory__)
    def __default_factory__(self,dev_name):
        '''
        Called by defaultdict_fromkey.__missing__ method
        If a key doesn't exists this method is called and returns a proxy for a given device.
        If the proxy caused an exception (usually because device doesn't exists) a None value is returned
        '''        
        if dev_name not in self.keys():
            self.log.debug( 'Getting a Proxy for %s'%dev_name)
            try:
                devklass,attrklass = (TAU.Device,TAU.Attribute) if USE_TAU else (PyTango.DeviceProxy,PyTango.AttributeProxy)
                dev = (attrklass if str(dev_name).count('/')==(4 if ':' in dev_name else 3) else devklass)(dev_name)
            except Exception,e:
                print('ProxiesDict: %s doesnt exist!'%dev_name)
                print traceback.format_exc()
                dev = None
        return dev
            
    def get(self,dev_name):
        return self[dev_name]   
    def get_admin(self,dev_name):
        '''Adds to the dictionary the admin device for a given device name and returns a proxy to it.'''
        dev = self[dev_name]
        class_ = dev.info().dev_class
        admin = dev.info().server_id
        return self['dserver/'+admin]
    def pop(self,dev_name):
        '''Removes a device from the dict'''
        if dev_name not in self.keys(): return
        self.log.debug( 'Deleting the Proxy for %s'%dev_name)
        return CaselessDefaultDict.pop(self,dev_name)