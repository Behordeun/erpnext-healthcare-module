// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt

frappe.ui.form.on('FamilyHistory', {
	refresh: function(frm) {
    frm.set_query(
      "reason_reference_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Condition", "Observation", "AllergyIntolerance", "QuestionnaireResponse", "DiagnosticReport", "DocumentReference"]
        ]
      ])
    );
	}
});
