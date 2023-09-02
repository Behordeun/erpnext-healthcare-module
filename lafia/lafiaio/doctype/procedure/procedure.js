// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt
const setQuery = function (filters) {
	return {
		filters
	};
}

frappe.ui.form.on("Procedure Report Table", {
  refresh: function (frm) {

    frm.set_query(
      "report_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Diagnostic Report"]
        ]
      ])
    );
  }
})

frappe.ui.form.on("Performer", {
	refresh: function(frm) {
    frm.set_query(
      "subject_type",
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
})

frappe.ui.form.on("Procedure", {
  refresh: function (frm) {
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
      "asserter_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient_LafiaIO", "Practitioner", "PractitionerRole"]
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
          ["Patient_LafiaIO", "Practitioner", "PractitionerRole"]
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
          ["Condition", "Observation", "Procedure", "Diagnostic Report"]
        ]
      ])
    );

    frm.set_query(
      "basedon_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Care Plan", "Service Request"]
        ]
      ])
    );

    frm.set_query(
      "partof_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Observation", "Procedure", "Medication Administration"]
        ]
      ])
    );
  },
});
