// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt
const setQuery = function (filters) {
	return {
		filters
	};
}

frappe.ui.form.on('Adverse Event', {
	refresh: function(frm) {
    frm.set_query(
      "subject_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient", "Group", "Healthcare Practitioner", "Related Person"]
        ]
      ])
    );

    frm.set_query(
      "recorder_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient", "Healthcare Practitioner", "PractitionerRole", "Related Person"]
        ]
      ])
    );

	frm.set_query(
		"contributor_type",
		setQuery([
		  [
			"DocType",
			"name",
			"in",
			["Patient", "Healthcare Practitioner", "PractitionerRole", "Device"]
		  ]
		])
	  );

    frm.set_query(
      "subject_medical_history_type",
      setQuery([
        [
        "DocType",
        "name",
        "in",
        ["AllergyIntolerance", "Observation", "Condition", "FamilyMemberHistory", "Immunization", "Clinical Procedure", "Media", "DocumentReference"]
        ]
      ])
      );

	}
});
