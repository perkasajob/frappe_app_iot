from __future__ import unicode_literals
import frappe
from frappe import msgprint
from frappe.utils import nowdate
from frappe import utils
import json


@frappe.whitelist(allow_guest=True)
def getNodes():
    # return frappe.session.user
    # company = frappe.db.get_single_value("Global Defaults", "default_company")
    return {'usr':"perkasajob@gmail.com", 'pwd': "ssdd"}
    # return frappe.get_all('Node')
    # path = map(lambda x: company + '/' + x.name, devices)

@frappe.whitelist(allow_guest=True)
def getLogin():
    return {'usr':"perkasajob@gmail.com", 'pwd': "ssdd"}

@frappe.whitelist(allow_guest=True)
def getSomething():
    return {'usr':"perkasajob@gmail.com", 'pwd': "ssss"}    