frappe.provide('iot.testdashboard1');

$.fn.gauge = function(opts) {
	this.each(function() {
	  var $this = $(this),
		  data = $this.data();

	  if (data.gauge) {
		data.gauge.stop();
		delete data.gauge;
	  }
	  if (opts !== false) {
		data.gauge = new Gauge(this).setOptions(opts);
	  }
	});
	return this;
  };

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


if(typeof Chart === "undefined"){ // on production server is called frappeChart
	var Chart = frappeChart
}


function goToNode(selectedNode){
	nodeId = selectedNode
	loadConfigs(page.parent, nodeId)
	$('#selectNode').hide()
	// window.location.assign(window.location.href+"/?node="+selectedNode)
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
		title: 'testDashboard',
		single_column: true
	});


	nodeId = getUrlVars(window.location.href)['node']
	wrapper = wrapper

	console.log(page)
	page.add_menu_item('IOT', () => frappe.set_route('List','Node' ))

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
											chartData[s.viz_group] = charts[s.viz_group].data
											if (chartData[s.viz_group].labels[chartData[s.viz_group].labels.length-1] !== date)
												chartData[s.viz_group].labels.push(date)
											chartData[s.viz_group].datasets.map((dataset, i) =>{
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
											$('#'+s.elId).val(s.value)
											$('#'+s.elId+'-text').html(s.label + ': ' + s.value.toFixed(s.f_prec) +' '+ unit)
											break;
										default:
										  $('#'+s.elId).html(s.value.toFixed(s.f_prec))
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
			'assets/css/iot.custom.css',
			//'assets/testdashboard1/css/setup.css'
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
			if(s.visualization !== 'hidden' && s.visualization !== 'chart' && !s.viz_group){
				data.push({header : s.label, dataId: dataId, children:[s], width: s.card_width, visualization: s.visualization, unit: s.unit })
				dataId += 1
			}
		})

		$(frappe.render_template('testdashboard1', {nodes:nodes })).appendTo(this.wrapper);
		// $("canvas").forEach(canvas=>{
		// 	resizeCanvasToDisplaySize(canvas)
		// })

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
						if(signal.visualization === 'chart' && signal.viz_group === key){
							datasets.push({name: signal.label + '('+ signal.unit +')', chartType: 'line', values: [] })
						}
					})



					charts[key] = new Chart('#chart'+key.replace(/\s/g,''),{
						lineOptions: {
							hideDots: 1 // default: 0
						},
						data: {
							labels: [],
							datasets: datasets,
							type: 'axis-mixed', // or 'bar', 'line', 'scatter', 'pie', 'percentage'
							height: 300,
							colors: ['#7cd6fd', '#743ee2','purple', '#ffa3ef', 'light-blue']
						}
					})
				}


				$(".grid").fadeIn()
				var grid = new Muuri('.grid', {
					dragEnabled: true,
					layoutOnInit: false
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
						gauge.maxValue = 3000; // set max gauge value
						gauge.setMinValue(0);  // set min value
						gauge.set(0); // set actual value

						gauges[signal.elId] = gauge
						$("#"+signal.elId).width($("#"+signal.elId).parent().width())
						// $("#"+signal.elId).height($("#"+signal.elId).parent().height())

					}
				})
				// setTimeout(function () {charts.forEach(chart =>{ chart.draw(!0)})}, 2);
			// });
		// })
	}
}