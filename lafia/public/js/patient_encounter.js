frappe.ui.form.on('Patient Encounter', {
	refresh(frm) {
		frm.toggle_display(['sb_symptoms','invoiced'], false);
		frm.remove_custom_button('Schedule Admission');
		frm.add_custom_button(__('Condition'), function() {
				create_condition(frm);
			},'Create');
	}
});

let create_condition = function(frm) {
	if (!frm.doc.patient) {
		frappe.throw(__('Please select patient'));
	}
	frappe.route_options = {
		'subject': frm.doc.patient,
		'encounter': frm.doc.name,
		'company': frm.doc.company
	};
	frappe.new_doc('Condition');
};