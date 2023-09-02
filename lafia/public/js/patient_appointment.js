frappe.ui.form.on('Patient Appointment', {
	refresh(frm) {
		frm.toggle_display(['appointment_type','procedure_template','get_procedure_from_encounter','therapy_plan','naming_series'], false);
		frm.set_df_property('duration', 'read_only', 1)
		
		if (frm.doc.status == 'Open' || (frm.doc.status == 'Scheduled' && !frm.doc.__islocal)) {
			frappe.call({
				method: "lafia.api.appointment.appointment.check_response",
				args: { name: frm.doc.name },
				callback: function(r) {
					if (!r.message) {
						frm.add_custom_button(__('Accept'), function() {
							create_response(frm, 'Accepted');
						});
					}
				}
			});
			
		}
	}
});

let create_response = function(frm, status) {
	let docs = frm.doc;
	console.log(docs)
	frappe.confirm(__('Are you sure you want to accept this appointment?'),
		function() {
			frappe.call({
				method: 'lafia.api.appointment.appointment.create_appointment_response',
				args: { doc: docs, status: status },
				callback: function(data) {
					if (!data.exc) {
						frappe.msgprint("Appointment has been accepted")
						frm.reload_doc();
					}
				}
			});
		}
	);
};
