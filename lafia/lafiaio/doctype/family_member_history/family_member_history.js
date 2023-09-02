// // Copyright (c) 2022, ParallelScore and contributors
// // For license information, please see license.txt

// frappe.ui.form.on('Family Member History', {
// 	// refresh: function(frm) {

// 	// }
// 	onload: function (frm) {
// 		if (frm.doc.born_date) {
// 			$(frm.fields_dict['age_html'].wrapper).html(`${__('AGE')} : ${get_age(frm.doc.born_date)}`);
// 		} else {
// 			$(frm.fields_dict['age_html'].wrapper).html('');
// 		}
// 	}
// });

// frappe.ui.form.on('Family Member History', 'born_date', function(frm) {
// 	if (frm.doc.born_date) {
// 		let today = new Date();
// 		let birthDate = new Date(frm.doc.born_date);
// 		if (today < birthDate) {
// 			frappe.msgprint(__('Please select a valid Date'));
// 			frappe.model.set_value(frm.doctype,frm.docname, 'born_date', '');
// 		} else {
// 			let age_str = get_age(frm.doc.born_date);
// 			$(frm.fields_dict['age_html'].wrapper).html(`${__('AGE')} : ${age_str}`);
// 		}
// 	} else {
// 		$(frm.fields_dict['age_html'].wrapper).html('');
// 	}
// });

// let get_age = function (birth) {
// 	let ageMS = Date.parse(Date()) - Date.parse(birth);
// 	let age = new Date();
// 	age.setTime(ageMS);
// 	let years = age.getFullYear() - 1970;
// 	return years + ' Year(s) ' + age.getMonth() + ' Month(s) ' + age.getDate() + ' Day(s)';
// };
