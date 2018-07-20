# -*- coding: utf-8 -*-
# Copyright (c) 2018, JETFOX - PT.Perkasa Jaya Kirana and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json, requests

class Node(Document):
	pass

#method : iot.iot.doctype.node.get_kibana
@frappe.whitelist()
def get_kibana(doctype_name, name):
	pass
	# return('<div> HELLO THERE !! </div>')
	# r =  requests.get('https://jetfox.co:5601/app/kibana#/dashboard/9dfd50e0-831b-11e8-aae9-e1d82298021a?_g=(refreshInterval%3A(display%3AOff%2Cpause%3A!f%2Cvalue%3A0)%2Ctime%3A(from%3Anow-60d%2Cmode%3Aquick%2Cto%3Anow))', stream=True)
	# return r.content
    
	# pass
