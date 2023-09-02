// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt
const setQuery = function (filters) {
	return {
		filters
	};
}

frappe.ui.form.on("AllergyIntolerance", {
  refresh: function (frm) {
    frm.set_query(
      "recorder_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient_LafiaIO", "Practitioner", "PractitionerRole"],
        ],
      ])
    );

    frm.set_query(
      "asserter_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient_LafiaIO", "Practitioner", "PractitionerRole"],
        ],
      ])
    );
  },
});
