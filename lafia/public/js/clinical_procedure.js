frappe.ui.form.on('Clinical Procedure', {
	refresh(frm) {
		frm.toggle_display(['invoiced','sample','consumables_section','naming_series'], false);
	}
})