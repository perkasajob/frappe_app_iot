from __future__ import unicode_literals
import frappe
from frappe import msgprint
from frappe.utils import nowdate
from frappe import utils
import json, requests
from elasticsearch import Elasticsearch
from frappe.utils import getdate, cstr, flt
from iot.iot.connection import iotSendCommand, iotMPublish


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
    return node

@frappe.whitelist(allow_guest=True)
def getNodes():
    node = frappe.get_all("Node")
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
            print(val +" : Not a float")
    return signalScaling


@frappe.whitelist(allow_guest=True)
def getDeviceConfig(node_id):
    from collections import OrderedDict
    res = OrderedDict()
    node = frappe.get_doc("Node", node_id)
    for signal in node.signal:
        dat = {'name' : signal.name, 'type': signal.data_type, 'label': signal.label.replace(" ", "_"), 'rw': signal.rw, 'scaling': parseSignalScalingFloat(signal.scaling), 'offset': signal.offset, 'unit': signal.unit, 'min': signal.min, 'max': signal.max, 'alarm_min': signal.alarm_min, 'alarm_max': signal.alarm_max }
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

    ws = frappe.get_doc("Work Shift Settings")

    work_shift = {'shift_1_start': ws.shift_1_start, 'shift_1_end': ws.shift_1_end,\
                  'shift_2_start': ws.shift_2_start, 'shift_2_end': ws.shift_2_end,\
                  'shift_3_start': ws.shift_3_start, 'shift_3_end': ws.shift_3_end }

    return {"db_filename": "device.db",\
        "clientId" : node.name,
        "topic": node.topic.replace('#', node.name),
        "thingName": node.name,
        "devices" : res,
        "work_shift": work_shift,
        "scan_interval": node.scan_interval,
        "send_trigger": node.send_trigger,
        "immediate_start": node.immediate_start,
        "enable_alarms": node.enable_alarms,
        "interval_alarms": node.interval_alarms, # hour
        "time_offset" : node.time_offset  # microseconds
    }

@frappe.whitelist(allow_guest=True)
def getPLCInterface(node_id):
    from collections import OrderedDict
    res = OrderedDict()
    node = frappe.get_doc("Node", node_id)
    for signal in node.signal:
        dat = {'type': signal.data_type, 'label': signal.label.replace(" ", "_"), 'rw': signal.rw, 'scaling': signal.scaling, 'alarm_min': signal.alarm_min, 'alarm_max': signal.alarm_max}
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
        dat = {'type': signal.data_type, 'label': signal.label.replace(" ", "_"), 'rw': signal.rw, 'scaling': signal.scaling, 'offset': signal.offset, 'alarm_min': signal.alarm_min, 'alarm_max': signal.alarm_max}
        if signal.ip in res: res[signal.ip].append(dat)
        else: res[signal.ip]= [dat]

    for re in res:
        idx = {}
        strSignal = ''
        idx_alarm = 0
        for r in res[re]: # Alarms
            strSignal += 'AlarmDebouncer_{}(TRUE, {}, {}, {}, T#200ms); '.format(idx_alarm, r['label'], r['alarm_max'], r['alarm_min'])
            strSignal += 'alarms[{}] := AlarmDebouncer_{}.alarm; '.format(idx_alarm, idx_alarm)
            idx_alarm += 1
            # strSignal += 'TON_{}_min({}<{}, T#200ms);'.format(r['label'], r['label'], r['alarm_max'])
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



@frappe.whitelist()
def getSignalList(node_id):
    node = frappe.get_doc("Node", node_id)
    data = []
    for signal in node.signal:
        data.append({'label': signal.label, 'ip': signal.ip.replace(".", "_"), "data_type": signal.data_type})
    return data


@frappe.whitelist(allow_guest=True)
def workshiftsettings():
    return frappe.get_doc("Work Shift Settings")

@frappe.whitelist()
def getWebsocket():
    print(frappe.get_conf().get("site_name"))
    res = requests.get(frappe.get_conf().get("ws_address"))
    return json.loads(res.content)

@frappe.whitelist(allow_guest=True)
def getProductionOutput():
    es = Elasticsearch([frappe.get_conf().get("elastic_server")],scheme="https",
    port=443,)
    doc = {"size":0,"aggs":{"machine_performance":{"date_histogram":{"field":"id","interval":"8h","format":"yyyy-MM-dd HH:mm:ss","time_zone":"+07:00","offset":"+0h"},"aggs":{"max_output1":{"max":{"field":"192_168_1_128.M1_Product_Output"}},"max_output2":{"max":{"field":"192_168_1_128.M2_Product_Output"}},"adder":{"bucket_script":{"buckets_path":{"tmax_output1":"max_output1","tmax_output2":"max_output2"},"script":"params.tmax_output1 + params.tmax_output2"}}}}}}
    res = es.search(index="lionwings", body=doc)
    return res

@frappe.whitelist(allow_guest=True)
def getCertificatePath(node_id):
    payload= {"message": "Herzliche Grussen"}
    return iotMPublish()

    # return iotSendCommand(node_id, payload)



@frappe.whitelist(allow_guest=True)
def getItemInfo2(search_value=""):
    return frappe.db.sql("SELECT asset, sn.item_name, sn.item_code, status,sn.location,custodian,ta.purchase_date,repair_status,ar.description,maintenance_manager,maintenance_team FROM `tabSerial No` sn INNER JOIN `tabAsset` ta ON sn.asset=ta.name INNER JOIN `tabAsset Repair` ar ON sn.asset=ar.asset_name INNER JOIN `tabAsset Maintenance` am ON sn.asset=am.asset_name WHERE sn.name=%s",
	    					(search_value), as_dict=True)


@frappe.whitelist(allow_guest=True)
def getItemInfo(search_value=""):
    data = dict()

    if search_value:
        data = search_serial_or_batch_or_barcode_number(search_value)

    item_code = data.get("item_code") if data.get("item_code") else search_value
    serial_no = data.get("serial_no") if data.get("serial_no") else ""
    batch_no = data.get("batch_no") if data.get("batch_no") else ""
    barcode = data.get("barcode") if data.get("barcode") else ""
    res= {}
    res = {
		'items': res
		}

    if serial_no:
        asset = frappe.db.get_value("Asset", data['asset'], ['name', 'asset_name', 'item_name', 'item_code', 'status', 'location','custodian'], as_dict=True)
        repair = frappe.db.get_value('Asset Repair', {'asset_name': data['asset']}, ['name', 'asset_name', 'item_code' ,'repair_status', 'description'], as_dict=True)
        maintanance = frappe.db.get_value('Asset Maintenance', {'asset_name': data['asset']}, ['name', 'asset_name', 'maintenance_manager' ,'maintenance_team'], as_dict=True)
        res.update({
			'serial_no': serial_no,
            'asset': asset,
            'repair': repair,
            'maintenance': maintanance
		})


    if batch_no:
    	res.update({
			'batch_no': batch_no
		})

    if barcode:
    	res.update({
			'barcode': barcode
		})

    return res


def search_serial_or_batch_or_barcode_number(search_value):
	# search barcode no
	barcode_data = frappe.db.get_value('Item Barcode', {'barcode': search_value}, ['barcode', 'parent as item_code'], as_dict=True)
	if barcode_data:
		return barcode_data

	# search serial no
	serial_no_data = frappe.db.get_value('Serial No', search_value, ['name as serial_no', 'item_code', 'asset'], as_dict=True)
	if serial_no_data:
		return serial_no_data

	# search batch no
	batch_no_data = frappe.db.get_value('Batch', search_value, ['name as batch_no', 'item as item_code'], as_dict=True)
	if batch_no_data:
		return batch_no_data

	return {}