// Copyright (c) 2016, JETFOX - PT.Perkasa Jaya Kirana and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Signal Analysis"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"node",
			"label": __("Node"),
			"fieldtype": "Link",
			"options": "Node",
			"get_query": function() {
				return {
					"doctype": "Node"

				}
			},
		},{
			"fieldname":"signal",
			"label": __("Signal"),
			"fieldtype": "MultiSelect",
			get_data: function() {
				let node = $(":input[data-fieldname='node']").val()
				if (!node)
					return []
				// var projects = frappe.query_report.get_filter_value("project") || "";

				// const values = projects.split(/\s*,\s*/).filter(d => d);
				// const txt = projects.match(/[^,\s*]*$/)[0] || '';
				let data = [];

				frappe.call({
					type: "GET",
					method:'iot.iot.getSignalList',
					async: false,
					no_spinner: true,
					args: {
						node_id: node
					},
					callback: function(r) {
						if(r){
							for(let i=0; i < r.message.length; i++){
								data.push(r.message[i].label)
							}
						}
					}
				});
				return data;
			},
		},
	],
	// "tree": true,
	// "name_field": "account",
	// "parent_field": "parent_account",
	// "initial_depth": 3,
	onload: function(report) {
		// report.page.add_inner_button(__("Test Button"), function() {
		// 	var filters = report.get_values();
			// frappe.set_route('query-report', 'Accounts Payable', {company: filters.company});
		// });
	},
	refresh: function(report){
		$(".dt-scrollable").ready(adjustScrollbarWidth);
	},
	get_chart_data: function(columns, result) {
		return {
			data: {
				labels: result.map(d => d[0]),
				datasets: [{
					name: 'Avg',
					values: result.map(d => d[1])
				},{
					name: 'Min',
					values: result.map(d => d[2])
				},{
					name: 'Max',
					values: result.map(d => d[3])
				}]
			},
			type: 'line',
		}

	}
}

function adjustScrollbarWidth(){
	setTimeout(function(){
	   if($(".dt-scrollable").length)
		   $(".dt-scrollable").width($(".dt-scrollable").width()+15);
	   else
		  adjustScrollbarWidth()

	},500)
 }

 $(".dt-scrollable").ready(adjustScrollbarWidth);

