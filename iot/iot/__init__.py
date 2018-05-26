from __future__ import unicode_literals
import frappe
from frappe import msgprint
from frappe.utils import nowdate
from frappe import utils
import json

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

def getNodes():
    node = frappe.get_all("Node")
    print node
    return node    
