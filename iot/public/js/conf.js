// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide('iot');

// add toolbar icon
$(document).bind('toolbar_setup', function() {
	frappe.app.name = "IOT JETFLEX";

	frappe.help_feedback_link = '<p><a class="text-muted" \
		href="https://discuss.erpnext.com">Feedback</a></p>'


	$('.navbar-home').html('<img class="iot-icon" src="'+
			frappe.urllib.get_base_url()+'/assets/frappe/images/JetFlex.svg" />');

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

});
