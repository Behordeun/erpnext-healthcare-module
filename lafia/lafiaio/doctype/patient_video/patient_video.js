// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Patient Video', {
	refresh: function(frm) {
		frm.add_custom_button(__("Patient Encounter"), function() {
			frappe.route_options = {
				"patient": frm.doc.patient
			};
			frappe.set_route("List","Patient Encounter");
		});

	}
});
