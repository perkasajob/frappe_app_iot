# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "IOT",
			"color": "#008080",
			"icon": "octicon octicon-radio-tower",
			"type": "module",
			"link": "modules/IOT",
			"label": _("IOT")
		},
		{
			"module_name": "IOT Dashboard",
			"color": "#DAAD86",
			"icon": "octicon octicon-graph",
			"type": "page",
			"link": "dashboard_rt",
			"label": _("Dashboard")
		}
	]
