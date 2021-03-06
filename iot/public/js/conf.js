// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide('iot');

// add toolbar icon
$(document).bind('toolbar_setup', function() {
	frappe.app.name = "IOT JETFLEX";

	frappe.help_feedback_link = '<p><a class="text-muted" \
		href="https://discuss.erpnext.com">Feedback</a></p>'


	$('.navbar-home').html('<img class="iot-icon" src="'+
			frappe.urllib.get_base_url()+'/assets/iot/images/JetFlex.svg" />');

	$('[data-link="docs"]').attr("href", "https://frappe.github.io/erpnext/")
	$('[data-link="issues"]').attr("href", "https://github.com/frappe/erpnext/issues")


	// default documentation goes to erpnext
	// $('[data-link-type="documentation"]').attr('data-path', '/erpnext/manual/index');

	// additional help links for erpnext
	var $help_menu = $('.dropdown-help ul .documentation-links');

	$('<li><a data-link-type="forum" href="https://discuss.erpnext.com" \
		target="_blank">'+__('User Forum')+'</a></li>').insertBefore($help_menu);
	$('<li><a href="https://gitter.im/frappe/erpnext" \
		target="_blank">'+__('Chat')+'</a></li>').insertBefore($help_menu);
	$('<li><a href="https://github.com/frappe/erpnext/issues" \
		target="_blank">'+__('Report an Issue')+'</a></li>').insertBefore($help_menu);
	$('<li><a href="https://kompas.com" \
	target="_blank">'+__('Dashboard')+'</a></li>').insertAfter($help_menu);

});

// $(document).on("page-change", function() {
// 	$(function() {
// 		if($("#dashboardIcon").length == 0 && window.location.pathname == '/desk')
// 			$('#icon-grid').append('<div id="dashboardIcon" class="case-wrapper" data-name="Dashboard" data-link="dashboard_rt" title="Dashboard"> <div class="app-icon" style="background-color: #5CDB95" title="Dashboard"><i class="octicon octicon-graph" title="Social" style=""></i></div> <div class="case-label ellipsis"> <div class="circle module-count-social" data-doctype="" style="display: none;"> <span class="circle-text"></span> </div>  <span class="case-label-text">Dashboard</span> </div> </div>')
// 	})
// });




