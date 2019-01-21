
// import DataTable from 'frappe-datatable';
// frappe.provide("frappe.report_dump");
frappe.provide('iot.testdashboard1');
frappe.provide("frappe.views");
{% include 'iot/iot/page/testdashboard1/mydatatable.js' %}
// import RealtimeClient from '/public/js/RealtimeClient';

// var mqtt = frappe.require('https://unpkg.com/mqtt/dist/mqtt.min.js')
//https://norita.jetfox.co/api/resource/Node/PrintingMachine
// {"192_168_1_128":{"PM1_Machine_On":1,"PM1_Line_Speed":34,"PM1_Machine_Run":0},"id":1547106914466,"name":"PrintingMachine"}"
// {"192_168_1_128":{"D1":10.53434,"D2":100.2324,"PM1_Line_Speed":86,"A0":20, "Motor_RPM":1000.3434, "Battery_Level":1500.35344},"id":1547106914466,"name":"PrintingMachine"}
const LAST_WILL_TOPIC = 'last-will';
const MESSAGE_TOPIC = 'Norita/db/#';
const CLIENT_CONNECTED = 'client-connected';
const CLIENT_DISCONNECTED = 'client-disconnected';
const uuidv4 = () => {
	return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
	  var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
	  return v.toString(16);
	});
  }
const clientId = frappe.session.user_fullname+uuidv4();
const username = frappe.session.user
let configs={};
var charts = []
let chartDataset = []
var gauges = []
var texts = []
var hz_bars = []
var dials = []
var switches = []
var rtdata = {}
let viz_group = []
let chartPtNr = 10
let dataId = 0
let data=[]
let nodeId = ''
let nodes=[]
let page=null
let grid ={}


if(typeof Chart === "undefined"){ // on production server is called frappeChart
	var Chart = frappeChart.Chart
}


function goToNode(selectedNode){
	nodeId = selectedNode
	loadConfigs(page.parent, nodeId)
	window.location.assign(window.location.href+"/?node="+nodeId)
	$('#selectNode').hide()
	// window.location.reload()
}


function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}

function addData( obj, visualization ){
	// let dec_place = null
	for(key in obj){
		// if(!dec_place)
		// 	dec_place = obj.dec_place
		data.push({header : key, dataId: dataId, elId: visualization+key.replace(/\s/g,''), children:obj[key], width: obj[key][0].card_width, visualization: visualization})
		dataId += 1
	}
}

function addOnCard(obj){
	for(key in obj){
		data.push({header : key, dataId: dataId, elId: visualization+key.replace(/\s/g,''), visualization: visualization})
		dataId += 1
	}
}

function layoutMenu(e){
	let dataId = e.parentElement.parentElement.parentElement.getAttribute('data-id')
	$( "div[data-id*='"+ dataId +"']" ).removeClass("col-sm-6").addClass("col-sm-8")
	console.log(dataId)
}

function initialiseResize(e) {
	window.addEventListener('mousemove', startResizing, false);
   	window.addEventListener('mouseup', stopResizing, false);
}

function startResizing(e) {
   box.style.width = (e.clientX - box.offsetLeft) + 'px';
   box.style.height = (e.clientY - box.offsetTop) + 'px';
}
function stopResizing(e) {
    window.removeEventListener('mousemove', startResizing, false);
    window.removeEventListener('mouseup', stopResizing, false);
}

function serializeLayout(grid) {
	var itemIds = grid.getItems().map(function (item) {
	  return item.getElement().getAttribute('data-id');
	});
	return JSON.stringify(itemIds);
}

function saveLayout(grid) {
	var layout = this.serializeLayout(grid);
	window.localStorage.setItem('layout', layout);
}

function loadLayout(grid, serializedLayout) {
	var layout = JSON.parse(serializedLayout);
	var currentItems = grid.getItems();
	var currentItemIds = currentItems.map(function (item) {
	  return item.getElement().getAttribute('data-id')
	});
	var newItems = [];
	var itemId;
	var itemIndex;

	for (var i = 0; i < layout.length; i++) {
	  itemId = layout[i];
	  itemIndex = currentItemIds.indexOf(itemId);
	  if (itemIndex > -1) {
		newItems.push(currentItems[itemIndex])
	  }
	}

	grid.sort(newItems, {layout: 'instant'});
}

function chartsRedraw(charts, chartData){
	for (let key in chartData){
		if(chartData[key].labels.length > chartPtNr){
			chartData[key].labels.shift()
			chartData[key].datasets.map(dataset =>{
				return dataset.values.shift()
			})
		}
		charts[key].draw()
	}
}

function loadConfigs(wrapper, nodeId){
	$.ajax({
		url: "/api/resource/Node/" + nodeId,
		type: "GET",
		success: function(r){
			if(r.data) {
				console.log(r.data)
				if (nodeId){
					configs = r.data
					for(var i=0; i < configs.signal.length; i++ ){
						configs.signal[i].elId = configs.signal[i].label.replace(/\s/g, '_');
						configs.signal[i].ip = configs.signal[i].ip.replace('.','_')
						configs.signal[i].value = 0
					}
				} else{
					nodes = r.data
					if(nodes.length === 1)
						goToNode(nodes[0].name)
				}
			}
		}
	}).always(function() {
		wrapper.setup = new iot.testdashboard1.SetupHelper(wrapper);
		window.cur_setup = wrapper.setup;
	})
}



frappe.pages['testdashboard1'].on_page_load = function(wrapper) {
	page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Dashboard',
		single_column: true,
		set_document_title: false
	});

	nodeId = getUrlVars(window.location.href)['node']
	wrapper = wrapper

	page.add_menu_item('Nodes', () => frappe.set_route('List','Node' ))

	client = RealtimeClient(clientId, username)
	client.connect().then(() => {
		client.onMessageReceived((topic, message) => {

			if (topic.substring(0, MESSAGE_TOPIC.length-1) === MESSAGE_TOPIC.substring(0, MESSAGE_TOPIC.length-1)){
				let chartData = {}
				let date = new Date()
				// let date = new Date(message.id);
				date = date.getHours()+':'+date.getMinutes()+':'+date.getSeconds()
				for(k in message){
					if (typeof message[k] == 'object'){
						for (l in message[k]){
							rtdata[l] = message[k][l]
							configs.signal.map((s,i)=>{
								if (s.elId === l){
									s.value = message[k][l]
									let unit = s.unit?s.unit:''

									switch(s.visualization) {
										case 'chart':
											let chartKey = s.viz_group? s.viz_group: s.label
											chartData[chartKey] = charts[chartKey].data
											if (chartData[chartKey].labels[chartData[chartKey].labels.length-1] !== date)
												chartData[chartKey].labels.push(date)
											chartData[chartKey].datasets.map((dataset, i) =>{
												if (dataset.name.substring(0, s.label.length) === s.label)
													dataset.values.push(s.value)
												return dataset
											})
										  break;
										case 'dial':
											gauges[s.elId].set(s.value)
											$('#'+gauges[s.elId].canvas.id+'-text').html(s.value.toFixed(s.f_prec) +' '+ unit)
										    break;
										case 'switch':
											if(s.value)
												$('#'+s.elId).removeClass("red-led grey-led").addClass('green-led')
											else
												$('#'+s.elId).removeClass("green-led grey-led").addClass('red-led')
											break;
										case 'hz-bar':
											let value = (s.value/((s.max||100)-(s.min||0))*100).toFixed(s.f_prec)
											let label = s.viz_group?s.label + ': ':'' // if the it doesn't belong to group, add label, otherwise no label, only value is shown
											$('#'+s.elId).val(value)
											$('#'+s.elId+'-text').html(label + s.value.toFixed(s.f_prec) +' '+ unit)
											break;
										default:
										  $('#'+s.elId).html(s.value.toFixed(s.f_prec)+" "+s.unit)
									  }
								}

								return s
							})

						}
					}
				}
				chartsRedraw(charts, chartData)
			}
			console.log(topic+ " ==> "+ JSON.stringify(message))
		})
		client.onDisconnect = (callback) => {
			console.log("Connection got disconneted ")
			setTimeout(function () {client.connect()}, 2)
		}
	})
	if(!nodeId){
		nodeId=''
	}

	loadConfigs(wrapper, nodeId)
}



iot.testdashboard1.SetupHelper = class SetupHelper {
	constructor(wrapper) {
		this.wrapper = $(wrapper).find('.layout-main-section');
		this.page = wrapper.page;

		const assets = [
			'assets/jetfox/frappe-datatable.js',
			'assets/jetfox/frappe-datatable.css',
			'assets/css/iot.custom.css',
		];

		frappe.require(assets, () => {
			if(nodeId)
				this.make();
			else
				this.createSelectNode()

		});
	}

	createSelectNode(){
		$(frappe.render_template('selectNode', {data:data })).appendTo(this.wrapper);
	}

	make() {
		this.prepare_charts();
		this.make_charts();
	}

	prepare_charts() {
		this.wrapper.append(`
			<div id="bddashboard"></div>
		`);
	}

	make_charts() {
		this.dashboard = new Dashboard({
			wrapper: this.wrapper.find('#bddashboard')
		});
	}

};

class Dashboard {
	constructor({ wrapper }) {
		this.wrapper = wrapper;
		this.make();
	}

	make() {
		this.prepare_charts();
		this.make_dom();

		// Making charts

		this.make_charts();

	}

	prepare_charts(){
		let viz ={ chart:[], text:[], dial:[], hz_bar:[], switch:[]}
		configs.signal.forEach((signal, i)=>{
			if (!signal.viz_group)
				return

			switch (signal.visualization) {
				case 'chart':
					if(!viz.chart.includes(signal.viz_group)) {
						viz.chart.push(signal.viz_group)
						charts[signal.viz_group] = []
						charts[signal.viz_group].push(signal)
					}
					break;
				case 'text':
					if(!viz.text.includes(signal.viz_group)) {
						viz.text.push(signal.viz_group)
						texts[signal.viz_group]=[]
					}
					texts[signal.viz_group].push(signal)
					break;
				case 'dial':
					if(!viz.dial.includes(signal.viz_group)) {
						viz.dial.push(signal.viz_group)
						dials[signal.viz_group]=[]
					}
					dials[signal.viz_group].push(signal)
					break;
				case 'hz-bar':
					if(!viz.hz_bar.includes(signal.viz_group)) {
						viz.hz_bar.push(signal.viz_group)
						hz_bars[signal.viz_group]=[]
					}
					hz_bars[signal.viz_group].push(signal)
					break;
				case 'switch':
					if(!viz.switch.includes(signal.viz_group)) {
						viz.switch.push(signal.viz_group)
						switches[signal.viz_group]=[]
					}
					switches[signal.viz_group].push(signal)
					break;
				default:
					break;
			}
		})
	}

	make_dom() {
		addData(charts, 'chart')
		addData(texts, 'text')
		addData(dials, 'dial')
		addData(switches, 'switch')
		addData(hz_bars, 'hz-bar')

		configs.signal.forEach(s =>{
			if(s.visualization !== 'hidden' && !s.viz_group){ //&& s.visualization !== 'chart'
				if (s.visualization === 'chart'){ // if chart doesn't belong to a viz group, then use label as the key
					data.push({header : s.label+'('+s.unit+')', dataId: dataId, elId: 'chart'+s.label.replace(/\s/g,''), children:[s], width: s.card_width, visualization: s.visualization })
					charts[s.label] = [s]
				} else {
					data.push({header : s.label, dataId: dataId, children:[s], width: s.card_width, visualization: s.visualization, unit: s.unit })
				}
				dataId += 1
			}
		})

		$(frappe.render_template('testdashboard1', {nodes:nodes })).appendTo(this.wrapper);
	}


	make_charts() {

		// $.getScript( "https://unpkg.com/hammerjs@2.0.8/hammer.min.js" )
		// .done(()=>{
		// 	$.when(
		// 		$.getScript( "https://unpkg.com/web-animations-js@2.3.1/web-animations.min.js" ),
		// 		$.getScript( "https://unpkg.com/muuri@0.7.1/dist/muuri.min.js" ),
		// 		$.Deferred(function( deferred ){
		// 			$( deferred.resolve );
		// 		})
		// 	).done(function(){

				let opts = {
					angle: 0.15, // The span of the gauge arc
					lineWidth: 0.44, // The line thickness
					radiusScale: 1, // Relative radius
					pointer: {
						length: 0.6, // // Relative to gauge radius
						strokeWidth: 0.035, // The thickness
						color: '#000000' // Fill color
					},
					limitMax: false,     // If false, max value increases automatically if value > maxValue
					limitMin: false,     // If true, the min value of the gauge will be fixed
					colorStart: '#FFFFFF',   // Colors
					colorStop: '#35F705',    // just experiment with them
					strokeColor: '#E0E0E0',  // to see which ones work best for you
					generateGradient: true,
					highDpiSupport: true,     // High resolution support
					staticLabels: {
						font: "10px sans-serif",  // Specifies font
						labels: [0, 1000, 1500, 2200.1, 2600, 3000],  // Print labels at these values
						color: "#000000",  // Optional: Label text color
						fractionDigits: 0  // Optional: Numerical precision. 0=round off.
						},

					};

				// viz_group = [...new Set(viz_idx)]; // get unique visualization group

				for( let key in charts){
					let datasets = []
					configs.signal.forEach(signal => {
						if(signal.visualization === 'chart' && signal.viz_group === key ){
							datasets.push({name: signal.label + '('+ signal.unit +')', type: 'line', values: [] })
						}
					})

					if(datasets.length === 0){ // if it is not a viz group, then search for label
						configs.signal.forEach(signal => {
							if(signal.visualization === 'chart' && !signal.viz_group && signal.label === key){
								datasets.push({name: signal.label + '('+ signal.unit +')', type: 'line', values: [] })
							}
						})
					}


					charts[key] = new Chart('#chart'+key.replace(/\s/g,''),{
						lineOptions: {
							hideDots: 0 // default: 0
						},
						data: {
							labels: [],
							datasets: datasets,
							type: 'axis-mixed', // or 'bar', 'line', 'scatter', 'pie', 'percentage'
							height: 300,
						},
						colors: ['#7cd6fd', '#743ee2','purple', '#ffa3ef', 'light-blue']
					})
				}


				$(".grid").fadeIn()
				grid = new Muuri('.grid', {
					dragEnabled: true,
					layoutOnInit: false,
					dragStartPredicate: {
						handle: '.octicon-three-bars'
					}
				}).on('move', function () {
					saveLayout(grid)
				});

				var layout = window.localStorage.getItem('layout');
				if (layout) {
					loadLayout(grid, layout);
				} else {
					grid.layout(true);
				}

				configs.signal.forEach((signal)=>{
					if(signal.visualization === 'dial'){
						var target = document.getElementById(signal.elId);
						opts.staticLabels.labels = [signal.min, signal.max]
						// console.log(opts.staticLabels.labels)
						var gauge = new Gauge(target).setOptions(opts); // create sexy gauge!
						gauge.maxValue = signal.max||100; // set max gauge value
						gauge.setMinValue(signal.min||0);  // set min value
						gauge.set(0); // set actual value

						gauges[signal.elId] = gauge
						$("#"+signal.elId).width($("#"+signal.elId).parent().width())
						// $("#"+signal.elId).height($("#"+signal.elId).parent().height())

					}
				})

				// const datatable = new DataTable('#datatable', {
				// 	columns: ['Name', 'Position', 'Salary'],
				// 	data: [
				// 	  ['Faris', 'Software Developer', '$1200'],
				// 	  ['Manas', 'Software Engineer', '$1400'],
				// 	]
				//   });
				// setTimeout(function () {charts.forEach(chart =>{ chart.draw(!0)})}, 2);
			// });
		// })
	}
}

// iot.SupportAnalytics = frappe.views.GridReportWithPlot.extend({
// 	init: function(wrapper) {
// 		this._super({
// 			title: __("Support Analtyics"),
// 			parent: $(wrapper).find('.layout-main'),
// 			page: wrapper.page,
// 			doctypes: ["Issue", "Fiscal Year"],
// 		});
// 	},

// 	filters: [
// 		{fieldname: "fiscal_year", fieldtype:"Select", label: __("Fiscal Year"), link:"Fiscal Year",
// 			default_value: __("Select Fiscal Year") + "..."},
// 		{fieldname: "from_date", fieldtype:"Date", label: __("From Date")},
// 		{fieldname: "to_date", fieldtype:"Date", label: __("To Date")},
// 		{fieldname: "range", fieldtype:"Select", label: __("Range"),
// 			options:["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"], default_value: "Monthly"}
// 	],

// 	init_filter_values: function() {
// 		this._super();
// 		this.filter_inputs.range.val('Monthly');
// 	},

// 	setup_columns: function() {
// 		var std_columns = [
// 			{id: "name", name: __("Status"), field: "name", width: 100},
// 		];
// 		this.make_date_range_columns();
// 		this.columns = std_columns.concat(this.columns);
// 	},

// 	prepare_data: function() {
// 		// add Opening, Closing, Totals rows
// 		// if filtered by account and / or voucher
// 		var me = this;
// 		var total_tickets = {name:"All Tickets", "id": "d-tickets",
// 			checked:true};
// 		var days_to_close = {name:"Days to Close", "id":"days-to-close",
// 			checked:false};
// 		var total_closed = {};
// 		var hours_to_close = {name:"Hours to Close", "id":"hours-to-close",
// 			checked:false};
// 		var hours_to_respond = {name:"Hours to Respond", "id":"hours-to-respond",
// 			checked:false};
// 		var total_responded = {};


// 		$.each(frappe.report_dump.data["Issue"], function(i, d) {
// 			var dateobj = frappe.datetime.str_to_obj(d.creation);
// 			var date = d.creation.split(" ")[0];
// 			var col = me.column_map[date];
// 			if(col) {
// 				total_tickets[col.field] = flt(total_tickets[col.field]) + 1;
// 				if(d.status=="Closed") {
// 					// just count
// 					total_closed[col.field] = flt(total_closed[col.field]) + 1;

// 					days_to_close[col.field] = flt(days_to_close[col.field])
// 						+ frappe.datetime.get_diff(d.resolution_date, d.creation);

// 					hours_to_close[col.field] = flt(hours_to_close[col.field])
// 						+ frappe.datetime.get_hour_diff(d.resolution_date, d.creation);

// 				}
// 				if (d.first_responded_on) {
// 					total_responded[col.field] = flt(total_responded[col.field]) + 1;

// 					hours_to_respond[col.field] = flt(hours_to_respond[col.field])
// 						+ frappe.datetime.get_hour_diff(d.first_responded_on, d.creation);
// 				}
// 			}
// 		});

// 		// make averages
// 		$.each(this.columns, function(i, col) {
// 			if(col.formatter==me.currency_formatter && total_tickets[col.field]) {
// 				days_to_close[col.field] = flt(days_to_close[col.field]) /
// 					flt(total_closed[col.field]);
// 				hours_to_close[col.field] = flt(hours_to_close[col.field]) /
// 					flt(total_closed[col.field]);
// 				hours_to_respond[col.field] = flt(hours_to_respond[col.field]) /
// 					flt(total_responded[col.field]);
// 			}
// 		})

// 		this.data = [total_tickets, days_to_close, hours_to_close, hours_to_respond];
// 	}
// });