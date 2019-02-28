from __future__ import unicode_literals
import frappe
from frappe import msgprint
from frappe.utils import nowdate
from frappe import utils
import json, requests, os
from frappe.utils import getdate, cstr, flt
from iot.iot.broker import ServerConnection


def on_message_received(message):
    try:
        print("Received Message From IOT Server")
        print(message)
        msg = json.loads(message)

    except Exception as e:
        return

sc = ServerConnection( \
    frappe.get_conf().get("iot_server"),\
    os.path.dirname(os.path.realpath(__file__))+'/root-CA.crt',
    'alpha_server',\
    frappe.get_conf().get("iot_alpha_topic") ,\
    'alpha_server', False)
sc.bindResponseMsg(on_message_received)


def iotPublish(topic=None, payload=None ):

    site_name = cstr(frappe.local.site)
    path = frappe.get_site_path('../crt/')
    caPath = path + "rootCA.pem"
    topic = site_name + "/" + topic
    certPath = path + "certificate.pem.crt"
    keyPath = path +"private.pem.key"
    endpoint = frappe.get_conf().get("iot_server")
    url= "https://" + endpoint+':8443/topics/'+topic

    parameters = (
        ('qos', '0'),
    )

    print("payload : " , payload)

    res = requests.post(url,params=parameters, json=payload, cert=(certPath,keyPath,caPath))
    return res

# Sending Command to device
def iotSendCommand(node_id, command):
    topic = "cmd/"+node_id
    payload = {"cmd": command}
    return iotPublish(topic, payload)


def iotMPublish():
    sc.publishValue({"cmd": 'update_config'}, topic="paci" + '/cmd/PLC1')
    return {"status":"sent"}
