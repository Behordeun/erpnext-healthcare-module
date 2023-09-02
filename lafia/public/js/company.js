frappe.ui.form.on('Company', {
	refresh(frm) {
		 frm.toggle_display(['section_break_28','default_settings','auto_accounting_for_stock_settings','fixed_asset_defaults','budget_detail','sales_settings','default_expense_claim_payable_account','default_employee_advance_account','default_payroll_payable_account'], false);
		 frm.clear_custom_buttons();
	}
});