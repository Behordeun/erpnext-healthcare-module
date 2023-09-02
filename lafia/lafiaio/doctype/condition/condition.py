# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os, json
from dotenv import load_dotenv
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_code_list, get_optional_doctype, get_code, \
	get_reference, get_identifier, get_practitioner, get_encounter,format_datetime
from frappe.utils import get_site_name,get_date_str
from lafia.api.services.brokers.producer import producer


load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Condition(Document):

	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()
			
			response = requests.post(
					lafia_base_url + '/Condition',
					json=fhir_schema)
			
			condition_object = response.json()
			frappe.errprint(condition_object)
		
			if response.status_code == 201:
				self.fhir_serverid = condition_object.get("id")
		
			else:
				frappe.throw("An error occured")

	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/Condition/' + self.fhir_serverid,
			json=fhir_schema)
			
		condition_object = response.json()
		print(condition_object)

	
	def after_insert(self):
		if self.notification_sent:
			event_body = {
				"resource_type": "Condition",
				"resource_id": self.fhir_serverid,
				"data": {
					"name": self.name,
					"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
					"id": self.fhir_serverid
				}
			}
			producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def on_trash(self):
		if self.fhir_serverid:
			response = requests.delete(
				lafia_base_url + '/Condition/' + self.fhir_serverid)		
			print(response.json())


	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Condition",
			"identifier": get_identifier(self.identifier) if self.identifier else "",
			"clinicalStatus": {"coding": [get_code("Condition Clinical Status", self.status)]} if self.status else "",
			"severity":  {"coding": [get_code("Condition Severity", self.severity)]} if self.severity else "",
			"code":  {"coding": [get_code("Condition Code", self.code)]} if self.code else "",
			"verificationStatus":  {"coding": [get_code("Condition Verification Status", self.verification_status)]} if self.verification_status else "",
			"category": [{"coding": [get_code("Condition Category", self.get("category"))]}] if self.get("category") else "",
			"bodySite": get_code_list("Body Site Code", self.get("body_site"), "body_site_code") if self.get("body_site") else "",
			"recorder": get_reference(self.recorder_ref, self.recorder) if self.recorder else "",
			#"asserter": get_reference(self.asserter_type, self.asserter.split("-")[2]) if self.asserter_type and self.asserter else "",
			"encounter": get_encounter(self.encounter) if self.encounter else "",
			"subject": get_reference("Patient", self.get("patient")),
			# "onsetDateTime": self.onset_datetime.replace(" ", "T") if self.onset_datetime else "",
			# "onsetPeriod": self.get_period(),
			# "abatementDateTime": self.abatement_datetime.replace(" ", "T") if self.abatement_datetime else "",
			# "abatementString": self.abatement_string,
			"recordedDate": format_datetime(self.recorded_date) if self.recorded_date else "",
			"note": [
				{
					"text": single_note.get("text"),
					"time": format_datetime(single_note.get("time"))
				} for single_note in self.get("note")
			] if self.get("note") else "",
			"participant": get_participant(self.get("participant"))

			# "period": get_period(self.period)
		}
		print(fhir_schema)

		return fhir_schema
	
	def get_period(self):
		return {
			'start': get_date_str(self.start),
			'stop': get_date_str(self.stop)
		}


def get_participant(participants):
	participant_list = []
	for part in participants:
		participant_list.append({
			"actor": get_practitioner(part.get("participant"))\
				if part.get("participant_role") == "Healthcare Practitioner"\
					else get_reference(part.get("participant_role"),part.get("participant")),
			"function": {
				"coding": [get_code("Participant Type", part.get("function"))]
				} if part.get("function") else ""
		})
	return participant_list

