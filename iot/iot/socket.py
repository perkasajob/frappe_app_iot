# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe import msgprint
import requests, json, pdb, os
from broker import ServerConnection


def on_message_received(message):
    try:
        msg = json.loads(message)
    except Exception as e:
        return


#os.environ.get('IOT_SERVER')
sc = ServerConnection( \
    frappe.get_conf().get("iot_server"),\
    os.path.dirname(os.path.realpath(__file__))+'/root-CA.crt',
    'alpha_server',\
    frappe.get_conf().get("iot_alpha_topic") ,\
    'alpha_server', False)
sc.bindResponseMsg(on_message_received)


def update_device_config(doc, method):
    # print('############### IOT ##########  ' +  os.environ.get('IOT_SERVER'))
    print(doc.name + " -----" + doc.topic +" the name")
    #sc.publishValue({"cmd": 'update_config'}, topic=doc.topic + '/cmd/' + doc.name)
    # frappe.publish_realtime('msgprint', os.environ.get('IOT_SERVER'))

def ping_device(doc, method):
    pass

