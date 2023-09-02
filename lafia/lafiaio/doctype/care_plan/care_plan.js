// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt
const setQuery = function (filters) {
	return {
		filters
	};
}

frappe.ui.form.on('Care Plan', {
	refresh: function(frm) {
    frm.set_df_property('category', 'fieldtype', 'Link');

    frm.set_query(
      "subject_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient_LafiaIO", "Group"]
        ]
      ])
    );

    frm.set_query(
      "author_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient_LafiaIO", "Practitioner", "PractitionerRole", "Device", "Organization"]
        ]
      ])
    );

	}
});
