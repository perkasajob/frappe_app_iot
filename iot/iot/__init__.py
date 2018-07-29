from __future__ import unicode_literals
import frappe
from frappe import msgprint
from frappe.utils import nowdate
from frappe import utils
import json, requests


@frappe.whitelist(allow_guest=True)
def getDevicesPath():
    # return frappe.session.user
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    devices = frappe.get_all('Node')
    print(company)
    # path = map(lambda x: company + '/' + x.name, devices)
    return company

@frappe.whitelist(allow_guest=True)
def getLogin():
    return {'usr':"perkasajob@gmail.com", 'pwd': "ssdd"}

@frappe.whitelist(allow_guest=True)
def registerNode(**args):
    data = args
    doc = frappe.get_doc({
        "doctype": "Node",
        "node_name": data['node_name'],
        "signals": data['signals'],
        "topic" : data['topic']
    })
    doc.insert(ignore_permissions=True)
    return doc

@frappe.whitelist(allow_guest=True)
def getNode(node_id):
    node = frappe.get_doc("Node", node_id)
    print node
    return node

@frappe.whitelist(allow_guest=True)
def getNodes():
    node = frappe.get_all("Node")
    print node
    return node

def convert2sqlite3Type(estype):
    if estype == 'boolean' or estype == 'integer' or estype == 'byte':
       return 'INT'
    elif estype == 'float' or estype == 'scaled_float':
       return 'REAL'
    elif estype =='text':
       return 'TEXT'
    else:
       return ''

def PLCTypeCasting(estype):
    if estype == 'boolean' or estype == 'integer' or estype == 'byte':
        return 'ANY_TO_BYTE'
    elif estype == 'integer':
        return 'ANY_TO_WORD'
    elif estype == 'float' or estype == 'scaled_float':
        return 'ANY_TO_REAL'
    elif estype =='text':
        return 'ANY_TO_TEXT'
    else:
        return ''

def parseSignalScalingFloat(val):
    signalScaling = 1.0
    if val != None:
        try:
            signalScaling = float(val)
        except ValueError:
            print val +" : Not a float"
    return signalScaling


@frappe.whitelist(allow_guest=True)
def getDeviceConfig(node_id):
    from collections import OrderedDict
    res = OrderedDict()
    node = frappe.get_doc("Node", node_id)
    for signal in node.signal:
        dat = {'type': signal.data_type, 'label': signal.label.replace(" ", "_"), 'rw': signal.rw, 'scaling': parseSignalScalingFloat(signal.scaling), 'offset': signal.offset }
        if signal.ip in res: res[signal.ip].append(dat)
        else: res[signal.ip]= [dat]

    for re in res:
        resRW = {'read':[], 'write':[]}
        for r in res[re]:
            rw = r['rw']
            resRW[rw].append(r)
        res[re] = resRW

    for re in res:
        for resw in res[re]:
            resType = OrderedDict()
            for r in res[re][resw]:
                estype = r['type']
                r['type'] = convert2sqlite3Type(r['type'])
                if estype == 'boolean' or estype == 'byte':
                    del r['scaling'] # dont need scaling for boolean or byte-digital
                    del r['offset']

                del r['rw']
                if estype == 'byte': # change byte to digital, since byte is reserved word in PLC Workbench
                   estype = 'digital'

                if estype in resType:
                    r['id'] = resType[estype][-1]['id'] + 1
                    resType[estype].append(r)
                else:
                    r['id'] = 0
                    resType[estype] = [r]
            res[re][resw]= resType


    return {"db_filename": "device.db",\
        "clientId" : node.name,
        "topic": node.topic.replace('#', node.name),
        "thingName": node.name,
        "devices" : res
    }

@frappe.whitelist(allow_guest=True)
def getPLCInterface(node_id):
    from collections import OrderedDict
    res = OrderedDict()
    node = frappe.get_doc("Node", node_id)
    for signal in node.signal:
        dat = {'type': signal.data_type, 'label': signal.label.replace(" ", "_"), 'rw': signal.rw, 'scaling': signal.scaling}
        if signal.ip in res: res[signal.ip].append(dat)
        else: res[signal.ip]= [dat]

    for re in res:
        idx = {}
        strSignal = ''
        for r in res[re]:
            estype = r['type']

            if estype == 'byte': # change byte to digital, since byte is reserved word in PLC Workbench
                estype = 'digital'

            if estype in idx:
                idx[estype] = idx[estype] + 1
            else:
                idx[estype] = 0
            strSignal += '{}[{}] :=  {}({});\n\r'.format(estype, idx[estype], PLCTypeCasting(r['type']), "* "+ r['label'] +" *")

        res[re]= strSignal
    return res

@frappe.whitelist(allow_guest=True)
def getPLCInterfaceWithScaling(node_id):
    from collections import OrderedDict
    res = OrderedDict()
    node = frappe.get_doc("Node", node_id)
    for signal in node.signal:
        dat = {'type': signal.data_type, 'label': signal.label.replace(" ", "_"), 'rw': signal.rw, 'scaling': signal.scaling, 'offset': signal.offset}
        if signal.ip in res: res[signal.ip].append(dat)
        else: res[signal.ip]= [dat]

    for re in res:
        idx = {}
        strSignal = ''
        for r in res[re]:
            estype = r['type']

            if estype == 'byte': # change byte to digital, since byte is reserved word in PLC Workbench
                estype = 'digital'

            if estype in idx:
                idx[estype] = idx[estype] + 1
            else:
                idx[estype] = 0
            typeCasting = PLCTypeCasting(r['type'])
            strScale =''
            if estype != 'digital':
                if r['scaling'] != None:
                    typeCasting, r['scaling']
                    strScale += '*{}({})'.format(typeCasting, r['scaling'])
                if r['offset'] != 0.0:
                    strScale += '+{}({})'.format(typeCasting, r['offset'])
            strSignal += '{}[{}] :=  {}({}){};\n\r'.format(estype, idx[estype], typeCasting, "* "+ r['label'] +" *", strScale)

        res[re]= strSignal
    return res



@frappe.whitelist(allow_guest=True)
def getESIndex_old(node_id):
    node = frappe.get_doc("Node", node_id)

    obj= { \
    'mappings': {    \
        'node': {    \
            'properties': {     \
                'data': {        \
                    'properties':{}\
                },\
                'name':{\
                'type': 'text'\
                }\
            }\
        },\
    }\
    }
    for s in node.signal:
        label = s.label.replace(" ", "_")
        if s.data_type == 'scaled_float':
            obj['mappings']['node']['properties']['data']['properties'][label]={'type': s.data_type, 'scaling_factor': 100}
        else:
            obj['mappings']['node']['properties']['data']['properties'][label]={'type': s.data_type}

    obj['mappings']['node']['properties']['data']['properties']['id'] = {'type' : 'date', 'format' :'epoch_millis'} # adding id as timestamp
    return obj

@frappe.whitelist(allow_guest=True)
def getESIndex(node_id):
    node = frappe.get_doc("Node", node_id)

    obj= { \
    'mappings': {    \
        'node': {    \
            'properties': {     \
                'id':{\
                'type' : 'date', 'format' :'epoch_millis'\
                },\
                'name':{\
                'type': 'text'\
                }\
            }\
        },\
    }
    }
    for s in node.signal:
        label = s.label.replace(" ", "_")
        ip = s.ip.replace(".","_")
        if ip not in obj['mappings']['node']['properties']:
            obj['mappings']['node']['properties'][ip] = {'properties' : {}}
        if s.data_type == 'scaled_float':
            obj['mappings']['node']['properties'][ip]['properties'][label]={'type': s.data_type, 'scaling_factor': 100}
        else:
            obj['mappings']['node']['properties'][ip]['properties'][label]={'type': s.data_type}

    return obj

