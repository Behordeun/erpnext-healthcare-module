// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Detected Issue', {
	// refresh: function(frm) {

	// }
});

frappe.ui.form.on('Detected Issue', {
	refresh: function(frm) {
    frm.set_query(
      "author_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Practitioner", "PractitionerRole", "Device"]
        ]
      ])
    );

	}
});
