// Copyright (c) 2023, ParallelScore and contributors
// For license information, please see license.txt

const setQuery = function (filters) {
	return {
		filters
	};
}

frappe.ui.form.on('Flag', {
	refresh: function(frm) {
    frm.set_query(
      "subject_ref",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Group","Location","Medication","Organization","Patient","PlanDefinition","Healthcare Practitioner","Clinical Procedure"]
        ]
      ])
    );

    frm.set_query(
      "author_ref",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient", "Healthcare Practitioner", "PractitionerRole", "Device","Organization"]
        ]
      ])
    );


	}
});
