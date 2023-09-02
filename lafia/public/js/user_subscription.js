$(document).on('app_ready', function() {
    frappe.call({
        method: "lafia.api.practitioner.practitioner.validate_subscription",
        callback: function(r) {
            console.log(r);
        }
    });
});
