# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "lafia"
app_title = "LafiaIO"
app_publisher = "ParallelScore"
app_description = "Integrations for lafia.io app"
app_icon = "octicon octicon-file-directory"
app_color = "purple"
app_email = "m.emereuwa@parallelscore.com"
app_license = "MIT"

website_context = {
	"splash_image": "/assets/lafia/images/lafia_logo.png"
}
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/lafia/css/lafia.desk.css"
# app_include_js = "/assets/lafia/js/lafia.js"
app_include_js = [
		"https://sdk.twilio.com/js/video/releases/2.8.0/twilio-video.min.js",
		"https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.1.2/socket.io.min.js",
		"https://cdnjs.cloudflare.com/ajax/libs/uuid/8.1.0/uuidv4.min.js",
		"/assets/lafia/js/call_patient.js",
		"/assets/lafia/js/chat_room.js",
        "/assets/lafia/js/user_subscription.js"
]

# include js, css files in header of web template
# web_include_css = "/assets/lafia/css/lafia.css"
web_include_js = [
	# "lafia-web.bundle.js",
  "/assets/lafia/node_modules/twilio-video/dist/twilio-video.min.js",
	"https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.1.2/socket.io.min.js",
  "/assets/lafia/node_modules/requirejs/require.js"
	]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lafia/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Patient" : "public/js/call_patient.js",
	"Chat Room": "api/chat_room/chat_room.js",
    "Patient Encounter": "public/js/patient_encounter.js",
    "Clinical Procedure": "public/js/clinical_procedure.js",
    "Company": "public/js/company.js",
    "Healthcare Practitioner": "public/js/healthcare_practitioner.js",
    "Practitioner Schedule": "public/js/practitioner_schedule.js",
    "Patient Appointment": "public/js/patient_appointment.js"
	}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "lafia.install.before_install"
# after_install = "lafia.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lafia.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Patient": {
		"before_insert": "lafia.api.patient.patient.patient_lafia_before_insert_script",
		"after_insert": "lafia.api.patient.patient.patient_lafia_after_save",
		"before_save": "lafia.api.patient.patient.patient_on_update",
	# 	"on_cancel": "method",
		"on_trash": "lafia.api.patient.patient.patient_on_delete"
	},
	"Healthcare Practitioner": {
		"before_insert": "lafia.api.practitioner.practitioner.practitioner_lafia_before_insert_script",
		"after_insert": "lafia.api.practitioner.practitioner.practitioner_lafia_after_save",
		"on_update": "lafia.api.practitioner.practitioner.practitioner_on_update",
		"on_trash": "lafia.api.practitioner.practitioner.practitioner_on_delete",
	},
	"Patient Encounter": {
		"before_insert": "lafia.api.encounter.encounter.encounter_before_insert_script",
		"after_insert": "lafia.api.encounter.encounter.encounter_after_save",
		"on_update": "lafia.api.encounter.encounter.encounter_on_update",
		"on_trash": "lafia.api.encounter.encounter.on_trash"
	},
	"User": {
		#"validate": "lafia.api.users.users.user_before_save"
	},
	"Clinical Procedure": {
		"before_insert": "lafia.api.procedure.procedure.procedure_before_insert",
		"after_insert": "lafia.api.procedure.procedure.procedure_after_insert",
		"on_update": "lafia.api.procedure.procedure.procedure_before_save",
		"on_trash": "lafia.api.procedure.procedure.on_delete"
	},
	# "Healthcare Service Unit": {
	# 	"before_insert": "lafia.api.service_unit.service_unit.before_insert",
	# 	"after_insert": "lafia.api.service_unit.service_unit.after_insert",
	# 	"on_update": "lafia.api.service_unit.service_unit.on_update",
	# 	"on_trash": "lafia.api.service_unit.service_unit.on_trash"
	# },
	"Patient Appointment": {
		"before_insert": "lafia.api.appointment.appointment.before_insert",
		"after_insert": "lafia.api.appointment.appointment.after_save",
		"on_update": "lafia.api.appointment.appointment.on_update",
		"on_trash": "lafia.api.appointment.appointment.on_delete"
	},
	"Practitioner Schedule": {
		"before_insert": "lafia.api.schedule.schedule.before_insert",
		"after_insert": "lafia.api.schedule.schedule.after_insert",
		"validate": "lafia.api.schedule.schedule.validate",
		"on_trash": "lafia.api.schedule.schedule.on_trash",
		"on_update": "lafia.api.schedule.schedule.on_update"
	},
    "Company": {
    	"before_insert": "lafia.api.service_unit.company.before_insert",
		"after_insert": "lafia.api.service_unit.company.after_insert",
		"on_update": "lafia.api.service_unit.company.on_update",
		# "on_trash": "lafia.api.service_unit.company.on_trash"
	},
    "Integration Request": {
		"on_update": "lafia.api.integration_request.integration_request.payment_entry"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		"lafia.api.services.brokers.consumers.consumer.patient_consumer",
        "lafia.tasks.all.add_perms",
        "lafia.tasks.all.delete_record_access"
        # "lafia.tasks.all.hide_modules"
	],
# 	"daily": [
# 		"lafia.tasks.daily"
# 	],
# 	"hourly": [
# 		"lafia.tasks.hourly"
# 	],
# 	"weekly": [
# 		"lafia.tasks.weekly"
# 	]
# 	"monthly": [
# 		"lafia.tasks.monthly"
# 	]
}

# Testing
# -------

# before_tests = "lafia.install.before_tests"

# Overriding Methods
# ------------------------------
override_doctype_class = {
	"User": "lafia.api.users.users.NewUser"
}
#
override_whitelisted_methods = {
	"frappe.core.doctype.user.user.update_password": "lafia.api.users.users.update_password",
    "frappe.desk.form.save.savedocs": "lafia.api.practitioner.practitioner.savedocs"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lafia.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

