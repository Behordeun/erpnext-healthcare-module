const setQuery = function (filters) {
	return {
		filters
	};
}

frappe.ui.form.on('Condition', {
	refresh: function(frm) {
    frm.set_query(
      "recorder_ref",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient", "Healthcare Practitioner"]
        ]
      ])
    );
	}
})
