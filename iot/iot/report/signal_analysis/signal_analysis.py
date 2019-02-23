# Copyright (c) 2013, JETFOX - PT.Perkasa Jaya Kirana and contributors
# For license information, please see license.txt

# Copyright (c) 2013, JETFOX - PT.Perkasa Jaya Kirana and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, time
from datetime import datetime, timedelta, date
import collections
from elasticsearch import Elasticsearch
from random import randint
from frappe.utils import getdate, cstr, flt
from frappe.utils import (convert_utc_to_user_timezone, now)

def execute(filters=None):
	columns, data = ['Date', 'Avg', 'Min', 'Max'], []
	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	if filters.signal:
		label, data = get_data(from_date, to_date, filters.node, filters.signal)

	return columns, data


def get_data(from_date, to_date, node, signal):
	site_name = cstr(frappe.local.site)
	print("#####################################################################")
	print(site_name)
	signal = signal.replace(",","").strip()
	sg_signal = frappe.get_all("Signal",filters={"parent":node, "label":signal}, fields=['ip','min' ,'max'] )[0]
	sg_signal_str = sg_signal.ip.replace('.','_') + '.' + signal.replace(" ", "_")

	es = Elasticsearch([frappe.get_conf().get("elastic_server")],scheme="https", port=443)
	# doc = {"size":0,"query":{"constant_score":{"filter":{"range":{"id":{"gte":from_date,"lte":to_date,"format":"yyyy-MM-dd","time_zone":"+07:00"}}}}},"aggs":{"signal":{"date_histogram":{"field":"id","interval":"8h","format":"yy-MM-dd HH:mm","time_zone":"+07:00","offset":"+0h"},"aggs":{"max_output1":{"max":{"field":"192_168_1_128.PM1_Line_signal"}}}}}}
	query = {"size":0,"query":{"constant_score":{"filter":{"range":{"id":{"gte":from_date,"lte":to_date,"format":"yyyy-MM-dd","time_zone":"+07:00"}}}}},"aggs":{"signal":{"date_histogram":{"field":"id","interval":"8h","format":"yy-MM-dd HH:mm","time_zone":"+07:00","offset":"+0h"},"aggs":{"signal_avg":{"avg":{"field":sg_signal_str}}, "signal_max":{"max":{"field":sg_signal_str}}, "signal_min":{"min":{"field":sg_signal_str}} }}}}
	res = es.search(index=site_name, body=query)
	res = res['aggregations']['signal']['buckets']


	label, data, d, avail, perf = [], [], {}, {}, {}
	timespan = 8*60 # in minutes since the signal is in minutes


	for r in res:
		if r['signal_avg']['value'] == None:
			continue

		utc_dt = datetime.utcfromtimestamp(r['key']/1000 - 1)
		t = convert_utc_to_user_timezone(utc_dt)
		date_str = t.strftime('%y-%m-%d')

		d[date_str] = [
			round(float(r['signal_avg']['value']),2),
			round(float(r['signal_min']['value']),2),
			round(float(r['signal_max']['value']),2),
		]

	od = collections.OrderedDict(sorted(d.items()))

	data = [[k]+v for k, v in od.items()]

	return label, data

def get_time_delta(t0, t1):
	return abs((datetime.combine(date.today(),t0) - datetime.combine(date.today(),t1)).total_seconds())
