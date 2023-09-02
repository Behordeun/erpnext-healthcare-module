$(function() {
	var module = {
		exports: {}
	}
	window.module = module;
	frappe.realtime.on('toconsole', function(data) {
		data.forEach(element => {
			console.log(element);
		});
	});
});