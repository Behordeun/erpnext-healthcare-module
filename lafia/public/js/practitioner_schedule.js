frappe.ui.form.on('Practitioner Schedule', {
	refresh(frm) {
		// your code here
		if (!frm.is_new()){
		    frm.toggle_display(['time_slots'], true);
		}
	}
});