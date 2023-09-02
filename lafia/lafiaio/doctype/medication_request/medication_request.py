# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os,json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code, get_reference, get_code_list,\
	format_datetime,get_reference_list,get_practitioner,get_annotation,get_reference_table
from lafia.api.services.brokers.producer import producer
from frappe.utils import get_site_name
from dotenv import load_dotenv
load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


class MedicationRequest(Document):
	def fhir_object(self):
		fhir_schema  = {
			"resourceType" : "MedicationRequest",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else [],
			"status": (self.status).lower(),
			"statusReason": {"coding": [get_code("Medication Request Status Reason", self.get("status_reason"))]} if self.get("status_reason") else "",
			"intent": (self.intent).lower(),
			"category": {"text":self.category},
			"priority": (self.priority).lower() if self.priority else "",
			"doNotPerform": True if self.do_not_perform else False,
			"medicationCodeableConcept": {"coding": [get_code("Medication Code", self.get("medication"))]} if self.get("medication") else "",
			"subject": get_reference("Patient",self.subject),
			"encounter": get_reference("Patient Encounter",self.encounter) if self.encounter else "",
			"authoredOn": format_datetime(self.date) if self.date else "",
			"supportingInformation": get_reference_table(self.get("supporting_information")) if self.get("supporting_information") else [],
			"requester": get_reference(self.requester_ref,self.requester) if self.requester else "",
			"performer": get_reference(self.performer_ref, self.performer) if self.performer else "",
			# "performerType": {"coding": [get_code("Performer Type", self.get("performer_type"))]} if self.get("performer_type") else "",
			"recorder": get_practitioner(self.recorder) if self.recorder else "",
			"reasonCode": get_code_list("Condition Code", self.get("reason_code"), "condition") if self.get("reason_code") else "",
			"reasonReference": get_reference_table(self.get("reason_reference")) if self.get("reason_reference") else [],
			"basedOn": get_reference_table(self.get("based_on")) if self.get("based_on") else [],
			"courseOfTherapyType": {"text": self.course_of_therapy_type},
			"insurance": get_reference_table(self.get("insurance")) if self.get("insurance") else [],
			# "note": get_annotation(self.get("note")) if self.get("note") else [],
			"priorPrescription": get_reference("Medication Request",self.prior_prescription) if self.prior_prescription else "",
			"dosageInstruction": self.get_dosage() if self.get('dosage_instruction') else []
		}
		frappe.errprint(fhir_schema)
		return fhir_schema
	
	def get_dosage(self):
		dosage_list = []
		for dosage in self.get('dosage_instruction'):
			dosage_list.append({
				"text": dosage.get("text")
			})
		return dosage_list


	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/MedicationRequest', json=fhir_schema)
			
			request_object = response.json()
			frappe.errprint(request_object)

			if response.status_code == 201:
				self.fhir_serverid = request_object.get("id")
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/MedicationRequest/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		request_object = response.json()
		print(request_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/MedicationRequest/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		if self.notification_sent:
			event_body = {
				"resource_type": "MedicationRequest",
				"resource_id": self.fhir_serverid,
				"data": {
					"name": self.subject,
					"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
					"id": self.fhir_serverid
				}
			}
			producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))
