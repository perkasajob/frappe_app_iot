# Copyright (c) 2013, JETFOX - PT.Perkasa Jaya Kirana and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, time
from datetime import datetime, timedelta, date
import collections
from elasticsearch import Elasticsearch
from random import randint
from frappe.utils import (convert_utc_to_user_timezone, now, get_site_name, getdate, cstr, flt)

def execute(filters=None):

	columns, data = ['Date','Shift 1', 'Shift 2', 'Shift 3'], []
	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)

	label, data = get_data2(from_date, to_date, filters.node, filters.signal)
	# for i in range(30):
	# 	data.append(['M'+str(i), 'location '+ str(i), 400+randint(0, 100), 400+randint(0, 100), 400+randint(0, 100)  ])

	# chart["type"] = "bar"

	# chart = {
	# 	"data": {
	# 		'labels': ["something"],
	# 		'datasets': rows
	# 	},
	# 	"type": 'line'
	# }

	return columns, data

def get_data2(from_date, to_date, node, signal):
	site_name = cstr(frappe.local.site)

	es = Elasticsearch([frappe.get_conf().get("elastic_server")],scheme="https", port=443)
	doc = {"size":0,"query":{"constant_score":{"filter":{"range":{"id":{"gte":from_date,"lte":to_date,"format":"yyyy-MM-dd","time_zone":"+07:00"}}}}},"aggs":{"machine_performance":{"date_histogram":{"field":"id","interval":"8h","format":"yy-MM-dd HH:mm","time_zone":"+07:00","offset":"+0h"},"aggs":{"max_output1":{"max":{"field":"192_168_1_128.M1_Product_Output"}},"max_output2":{"max":{"field":"192_168_1_128.M2_Product_Output"}},"adder":{"bucket_script":{"buckets_path":{"tmax_output1":"max_output1","tmax_output2":"max_output2"},"script":"params.tmax_output1 + params.tmax_output2"}}}}}}
	res = es.search(index=site_name, body=doc)
	res = res['aggregations']['machine_performance']['buckets']
	wss = frappe.get_doc("Work Shift Settings")

	t_end_shift1 = datetime.strptime(wss.shift_1_end, "%H:%M:%S").time()
	t_end_shift2 = datetime.strptime(wss.shift_2_end, "%H:%M:%S").time()
	t_end_shift3 = datetime.strptime(wss.shift_3_end, "%H:%M:%S").time()

	label, data, d = [], [], {}

	for r in res:
		if r['max_output1']['value'] == None:
			continue

		utc_dt = datetime.utcfromtimestamp(r['key']/1000 - 1)
		t = convert_utc_to_user_timezone(utc_dt)
		date_str = t.strftime('%y-%m-%d')

		if date_str not in d:
			d[date_str] = [0, 0, 0]

		if get_time_delta(t.time(), t_end_shift1) < 2 : #and (t_old.tm_mon != t.tm_mon or t_old.tm_mday != t.tm_mday or t_old.tm_year != t.tm_year)
			d[date_str][0] = int(r['max_output1']['value'])
			# print('shift 1: ' +  str(r['max_output1']['value']))
		elif get_time_delta(t.time(), t_end_shift2) < 2:
			d[date_str][1] = int(r['max_output1']['value'])
			# print('shift 2: ' +  str(r['max_output1']['value']))
		elif get_time_delta(t.time(), t_end_shift3) > 86280 or get_time_delta(t.time(), t_end_shift3) < 2: # 86280 = 23 hours*3600 + 58 min* 60
			if date_str not in d:
				d[date_str] = [0, 0, 0]
			d[date_str][2] = int(r['max_output1']['value'])
			# print('shift 3: ' +  str(r['max_output1']['value']))

	od = collections.OrderedDict(sorted(d.items()))

	data = [[k]+v for k, v in od.items()]

	return label, data

def get_time_delta(t0, t1):
	return abs((datetime.combine(date.today(),t0) - datetime.combine(date.today(),t1)).total_seconds())