# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"module_name": "IOT",
			"color": "#589494",
			"icon": "octicon octicon-graph",
			"type": "page",
			"link": "testdashboard1",
			"label": _("Dashboard1")
		},
		{
			"module_name": "IOT",
			"color": "green",
			"icon": "octicon octicon-radio-tower",
			"type": "module",
			"label": _("IOT")
		}
	]
