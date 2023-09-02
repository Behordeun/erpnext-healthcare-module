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

class MedicationDispense(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "MedicationDispense",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else [],
			"partOf": get_reference_list("Clinical Procedure",self.get("part_of"),"procedure") if self.get("part_of") else [],
			"status": (self.status).lower(),
			"statusReasonReference": get_reference("Detected Issue", self.get("status_reason_reference")) if self.get("status_reason_reference") else "",
			"category": {"text":self.category},
			"medicationReference": get_reference("Medication",self.medication_reference) if self.medication_reference else "",
			"subject": get_reference("Patient",self.patient),
			"context": get_reference("Patient Encounter",self.encounter) if self.encounter else "",
			"supportingInformation": get_reference_table(self.get("supporting_information")) if self.get("supporting_information") else [],
			"performer": self.get_performer() if self.get("performer") else [],
			"location": get_reference("Locations",self.location) if self.location else "",
			"authorizingPrescription": get_reference_list("Medication Request",self.authorizing_prescription,"request") if self.authorizing_prescription else [],
			"type": {"coding": [get_code("Supply Type", self.get("type"))]} if self.get("type") else "",
			"quantity": {"value":self.quantity},
			"daysSupply": {"value":self.days_supply},
			"whenPrepared": format_datetime(self.when_prepared) if self.when_prepared else "",
			"whenHandedOver": format_datetime(self.when_handed_over) if self.when_handed_over else "",
			"destination": get_reference("Locations",self.destination) if self.destination else "",
			"receiver": get_reference_table(self.get("receiver")) if self.get("receiver") else [],
			"note": get_annotation(self.get("note")) if self.get("note") else [],
			"substitution": self.get_substitution() if self.get("substitution") else {},
			"detectedIssue": get_reference_list("Detected Issue",self.detected_issue,"detected_issue") if self.detected_issue else ""
		}
		frappe.errprint(fhir_schema)
		return fhir_schema


	def get_performer(self):
		performer_list = []
		for performer in self.get("performer"):
			performer_list.append(
				{
					"function":{"text":performer.get("function")},
					"actor": get_reference(performer.get("actor_type"), performer.get("actor"))
				} 
			)
		return performer_list

	def get_substitution(self):
		return {
			"wasSubstituted": self.substituted,
			"type": {"coding": [get_code("Medication Substitution Type", self.get("substitution_type"))]} if self.get("substitution_type") else "",
			"reason": [{"text":self.substitution_reason}],
			"responsibleParty": [get_practitioner(self.practitioner_responsible)] if self.practitioner_responsible else ""
		}

	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/MedicationDispense', json=fhir_schema)
			
			dispense_object = response.json()
			frappe.errprint(dispense_object)

			if response.status_code == 201:
				self.fhir_serverid = dispense_object.get("id")
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/MedicationDispense/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		dispense_object = response.json()
		print(dispense_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/MedicationDispense/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "MedicationDispense",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.patient,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

