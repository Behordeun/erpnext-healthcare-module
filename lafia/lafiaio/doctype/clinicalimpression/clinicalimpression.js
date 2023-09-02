// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt
const setQuery = function (filters) {
	return {
		filters
	};
}

frappe.ui.form.on("ClinicalImpression", {
  refresh: function (frm) {
    frm.set_query(
      "subject_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient", "Group"]
        ]
      ])
    );

    frm.set_query(
      "assessor_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Practitioner", "PractitionerRole"]
        ]
      ])
    );

    frm.set_query(
      "problem_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Condition", "AllergyIntolerance"]
        ]
      ])
    );
	}
});
