// Copyright (c) 2021, ParallelScore and contributors
// For license information, please see license.txt
const setQuery = function (filters) {
	return {
		filters
	};
}

frappe.ui.form.on("Goal", {
  refresh: function (frm) {
    frm.set_query(
      "subject_type",
      setQuery([
        [
          "DocType",
          "name",
          "in",
          ["Patient_LafiaIO", "Group", "Organization"]
        ]
      ])
    );
	}
});
