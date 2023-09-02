# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe, os, requests, json
from frappe.utils import get_site_name
from frappe.model.document import Document
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier,get_code_list,get_reference,\
	format_datetime,get_practitioner,get_fhir_doc
from frappe.utils import get_site_name
from lafia.api.services.brokers.producer import producer
from healthcare.healthcare.doctype.patient_appointment.patient_appointment import update_status

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class AppointmentResponse(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "AppointmentResponse",
			"identifier": get_identifier(self.identifier) if self.identifier else "",
			"appointment": get_reference("Patient Appointment",self.appointment),
			"start": format_datetime(self.start) if self.start else "",
			"end": format_datetime(self.end) if self.end else "",
			"participantType": get_code_list("Participant Type Code", self.get("participant_type"), "participant_type_code") if self.get("participant_type") else "",
			"actor": get_practitioner(self.practitioner),
			"participantStatus": (self.status).lower(),
			"comment": self.comment		
		}
		return fhir_schema

	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/AppointmentResponse', json=fhir_schema)
			
			app_object = response.json()
			print(app_object)

			if response.status_code == 201:
				self.fhir_serverid = app_object.get('id')
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/AppointmentResponse/{0}'.format(self.fhir_serverid),json=fhir_schema)
			
		app_object = response.json()
		print(app_object)

		if self.status == "Declined":
			update_status(self.appointment,"Cancelled")

	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/AppointmentResponse/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		# if self.status == "Declined":
		# 	update_status(self.appointment,"Cancelled")

		if self.notification_sent:
			event_body = {
				"resource_type": "AppointmentResponse",
				"resource_id": self.fhir_serverid,
				"data": {
					"name": self.appointment_name,
					"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
					"id": self.fhir_serverid
				}
			}
			producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))


def appointment_response(doc):
	response = get_fhir_doc("Appointment Response",doc.get('id'))
	status = doc.get("participantStatus").capitalize()
	if response:
		response_doc = frappe.get_doc("Appointment Response",response)
		response_doc.db_set("status", status, commit=True)
		response_doc.save()
	
	else:
		split_appointment = doc.get('appointment').get("reference").split("/")
		split_actor = doc.get('actor').get("reference").split("/")
		response_doc_ = {
			"doctype": "Appointment Response",
			"appointment": get_fhir_doc("Patient Appointment",split_appointment[1]),
			"start": doc.get("start").replace("T", " ").replace("Z", ""),
			"end": doc.get("end").replace("T", " ").replace("Z", ""),
			"practitioner": get_fhir_doc("Healthcare Practitioner",split_actor[1]),
			# "practitioner_name": doc.practitioner_name,
			"participant_type": [{
				"participant_type_code": "attender"
			}],
			"status": status,
			"fhir_serverid": doc.get(id),
			"notification_sent": 0,
			"docstatus": 0
		}
		response_doc = frappe.get_doc(response_doc_)
		response_doc.insert()
		frappe.db.commit()
		print("appointment response created")
	