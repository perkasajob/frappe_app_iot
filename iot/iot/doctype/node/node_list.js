frappe.listview_settings['Node'] = {
	onload: function (listview) {
		listview.page.add_menu_item(__("Dashboard"), function () {
			window.location = window.location.origin + '/rtdash'
		});
	}
};