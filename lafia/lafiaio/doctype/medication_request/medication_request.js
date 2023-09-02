// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt

const setQuery = function (filters) {
	return {
		filters
	};
}

frappe.ui.form.on('Medication Request', {
	refresh: function(frm) {
    frm.set_query(
      "requester_ref",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Group","Patient","Organization","Healthcare Practitioner","Related Person"]
        ]
      ])
    );

    frm.set_query(
      "performer_ref",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["CareTeam","Organization","Patient", "Healthcare Practitioner", "PractitionerRole", "Device","Related Person"]
        ]
      ])
    );
      frm.add_custom_button(__('Create Medication Dispense'), function() {
        createDispense(frm);
      });
	}
});

let createDispense = function(frm) {
  frappe.route_options = {
    'patient': frm.doc.patient,
    'category': frm.doc.category,
    'authorizing_prescription': frm.doc.name
  }
  frappe.new_doc('Medication Dispense')
}
