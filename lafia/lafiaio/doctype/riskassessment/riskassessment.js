// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt

frappe.ui.form.on('RiskAssessment', {
	refresh: function(frm) {
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
		"performer_type",
		setQuery([
		  [
			"DocType",
			"name",
			"in",
			["Practitioner", "PractitionerRole", "Device"]
		  ]
		])
	  );

	  frm.set_query(
		"reason_reference_type",
		setQuery([
		  [
			"DocType",
			"name",
			"in",
			["Condition", "Observation", "DiagnosticReport", "DocumentReference"]
		  ]
		])
	  );

	  frm.set_query(
		"basis_type",
		setQuery([
		  [
			"DocType",
			"name",
			"in",
			[]
		  ]
		])
	  );

	  frm.set_query(
		"condition_type",
		setQuery([
		  [
			"DocType",
			"name",
			"in",
			["Condition"]
		  ]
		])
	  );
	}
});