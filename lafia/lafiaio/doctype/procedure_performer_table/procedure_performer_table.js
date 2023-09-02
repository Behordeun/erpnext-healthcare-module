

frappe.ui.form.on("Procedure Performer Table", {
	refresh: function(frm) {
    frm.set_query(
      "subject_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient_LafiaIO", "Practitioner", "PractitionerRole", "Device", "Organization"],
        ],
      ])
    );
	}
})