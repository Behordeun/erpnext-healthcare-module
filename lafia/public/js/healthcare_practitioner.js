frappe.ui.form.on('Healthcare Practitioner', {
	refresh(frm) {
		 frm.toggle_display(['accounts','address_and_contacts_section','residence_phone','office_phone','op_consulting_charge_item','inpatient_visit_charge_item','inpatient_visit_charge'], false);
		 frm.set_df_property('department', 'reqd', 1)
		 if (!frm.is_new()){
		    frm.set_df_property('register_as_employee', 'read_only', 1) 
		}
	}
});