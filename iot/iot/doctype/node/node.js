// Copyright (c) 2018, JETFOX - PT.Perkasa Jaya Kirana and contributors
// For license information, please see license.txt

frappe.ui.form.on('Node', {
	refresh: function(frm) {
		frm.add_custom_button(__('Dashboard'), function(){
			window.location = window.location.origin + '/rtdash?node=' + frm.docname
			
		});
	}	
});


