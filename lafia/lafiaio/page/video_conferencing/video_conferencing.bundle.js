frappe.pages['video_conferencing'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Video Conferencing',
		single_column: true
	});

	this.page.$VideoConferencing = new frappe.VideoConferencing.video_conferencing(this.page);

	$('div.navbar-fixed-top').find('.container').css('padding', '0');
	$("body").append("<div id='app'></div>")
	$("head").append("<link href='/assets/lafia/node_modules/vuetify/dist/vuetify.min.css' rel='stylesheet'>");
	$("head").append("<link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/@mdi/font@5.x/css/materialdesignicons.min.css' />"); 
	$("head").append("<link rel='stylesheet' href='https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900' />"); 

}