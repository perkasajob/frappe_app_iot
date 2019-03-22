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
	columns, data = ['Date','Shift 1', 'Shift 2', 'Shift 3', 'Avail(%)', 'Perf(%)', "OEE(%)"], []
	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	if filters.mOnOff and filters.speed:
		label, data = get_data(from_date, to_date, filters.node, filters.speed, filters.mOnOff)

	return columns, data

def get_data(from_date, to_date, node, speed, mOnOff):
	site_name = cstr(frappe.local.site)
	speed = speed.replace(",","").strip()
	mOnOff = mOnOff.replace(",","").strip()
	sg_speed = frappe.get_all("Signal",filters={"parent":node, "label":speed}, fields=['ip','min' ,'max'] )[0]
	sg_mOnOff = frappe.get_all("Signal",filters={"parent":node, "label":mOnOff}, fields=['ip'] )[0]
	sg_speed_str = sg_speed.ip.replace('.','_') + '.' + speed.replace(" ", "_")
	sg_mOnOff_str = sg_mOnOff.ip.replace('.','_') + '.' + mOnOff.replace(" ", "_")

	es = Elasticsearch([frappe.get_conf().get("elastic_server")],scheme="https", port=443)
	# doc = {"size":0,"query":{"constant_score":{"filter":{"range":{"id":{"gte":from_date,"lte":to_date,"format":"yyyy-MM-dd","time_zone":"+07:00"}}}}},"aggs":{"machine_performance":{"date_histogram":{"field":"id","interval":"8h","format":"yy-MM-dd HH:mm","time_zone":"+07:00","offset":"+0h"},"aggs":{"max_output1":{"max":{"field":"192_168_1_128.PM1_Line_Speed"}}}}}}
	query = {"size":0,"query":{"constant_score":{"filter":{"range":{"id":{"gte":from_date,"lte":to_date,"format":"yyyy-MM-dd","time_zone":"+07:00"}}}}},"aggs":{"machine_performance":{"date_histogram":{"field":"id","interval":"1d","format":"yy-MM-dd HH:mm","time_zone":"+07:00","offset":"+0h"},"aggs":{"avg_output1":{"avg":{"field":sg_speed_str}},"avg_pm_on1":{"avg":{"field":sg_mOnOff_str}},"pm_output":{"bucket_script":{"buckets_path":{"tavg_output1":"avg_output1","tavg_pm_on1":"avg_pm_on1"},"script":"params.tavg_output1 * params.tavg_pm_on1"}}}}}}
	res = es.search(index=site_name, body=query)
	res = res['aggregations']['machine_performance']['buckets']
	wss = frappe.get_doc("Work Shift Settings")

	t_start_shift1 = datetime.strptime(wss.shift_1_start, "%H:%M:%S").time()
	t_start_shift2 = datetime.strptime(wss.shift_2_start, "%H:%M:%S").time()
	t_start_shift3 = datetime.strptime(wss.shift_3_start, "%H:%M:%S").time()

	label, data, d, avail, perf = [], [], {}, {}, {}
	timespan = 8*60 # in minutes since the speed is in minutes


	for r in res:
		if r['avg_pm_on1']['value'] == None:
			continue

		utc_dt = datetime.utcfromtimestamp(r['key']/1000 - 1)
		t = convert_utc_to_user_timezone(utc_dt)
		date_str = t.strftime('%y-%m-%d')

		if date_str not in d:
			d[date_str] = [0, 0, 0, 0.0, 0.0, 0.0]
			avail[date_str] = 0 # helper to averaging availability
			perf[date_str] = 0

		# Averaging Availibility,
		avail[date_str] += float(r['avg_pm_on1']['value'])
		perf[date_str] += float(r['avg_output1']['value'])
		d[date_str][3] = round( avail[date_str]*100 / 3 ,1 ) # 3 is the shift sum is 3
		d[date_str][4] = round( perf[date_str]*100/sg_speed.max/3 , 1)
		d[date_str][5] = round( d[date_str][3]*d[date_str][4]/100 , 2) # OEE without defects calculation, divide by 100 to compensate one of percentage


		if get_time_delta(t.time(), t_start_shift1) < 2 : #and (t_old.tm_mon != t.tm_mon or t_old.tm_mday != t.tm_mday or t_old.tm_year != t.tm_year)
			d[date_str][0] = int(r['pm_output']['value'])*timespan
			# print('shift 1: ' +  str(r['pm_output']['value']))
		elif get_time_delta(t.time(), t_start_shift2) < 2:
			d[date_str][1] = int(r['pm_output']['value'])*timespan
			# print('shift 2: ' +  str(r['pm_output']['value']))
		elif get_time_delta(t.time(), t_start_shift3) > 86280 or get_time_delta(t.time(), t_start_shift3) < 2: # 86280 = 23 hours*3600 + 58 min* 60
			if date_str not in d:
				d[date_str] = [0, 0, 0]
			d[date_str][2] = int(r['pm_output']['value'])*timespan
			# print('shift 3: ' +  str(r['pm_output']['value']))


	od = collections.OrderedDict(sorted(d.items()))

	data = [[k]+v for k, v in od.items()]

	return label, data

def get_time_delta(t0, t1):
	return abs((datetime.combine(date.today(),t0) - datetime.combine(date.today(),t1)).total_seconds())