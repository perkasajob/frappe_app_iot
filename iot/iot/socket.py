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
        print e
        return


#os.environ.get('IOT_SERVER')
sc = ServerConnection( \
    'a38n08celxxznq.iot.us-east-1.amazonaws.com',\
    os.path.dirname(os.path.realpath(__file__))+'/root-CA.crt',
    'alpha_server',\
    'JetFlex/cmd/alphaServer' ,\
    'alpha_server', False)
print "Connecting ..................................................."
sc.bindResponseMsg(on_message_received)


def update_device_config(doc, method):
    print('############### IOT ##########  ' +  os.environ.get('IOT_SERVER'))
    print(doc.name + " ----- the name")
    sc.publishValue({"cmd": 'update_config'}, topic='paci/cmd/' + doc.name)
    frappe.publish_realtime('msgprint', os.environ.get('IOT_SERVER'))

def ping_device(doc, method):
    pass

