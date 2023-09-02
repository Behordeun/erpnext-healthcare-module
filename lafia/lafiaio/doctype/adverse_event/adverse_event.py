# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os,json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code, get_reference, get_code_list, get_optional_doctype,format_datetime,get_reference_list
from lafia.api.services.brokers.producer import producer
from dotenv import load_dotenv
load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class AdverseEvent(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "AdverseEvent",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
			"status": (self.status).lower(),
			"actuality": (self.get("actuality")).lower(),
			"category": get_code_list("Adverse Event Category", self.get("category"), "adverse_event_category") if self.get("category") else "",
			"code": {"coding": [get_code("Adverse Event Type", self.get("event"))]} if  self.event else "",
			"subject": get_reference(self.get("subject_type"), self.get("subject")),
			"encounter": get_reference("Patient Encounter", self.encounter) if self.get("encounter") else "",
			"occurrenceDateTime": format_datetime(self.occurrence_date) if self.occurrence_date else "",
			"detected": format_datetime(self.dectection_date) if self.get("dectection_date") else "",
			"recordedDate": format_datetime(self.recorded_date) if self.get("recorded_date") else "",
			"resultingCondition": get_reference_list("Condition",self.resulting_condition,'condition') if self.resulting_condition else "",
			"location": get_reference("Locations", self.location) if self.get("location") else "",
			"seriousness": {"text":self.seriousness} if self.seriousness else '',
			# "severity": get_code_list("Adverse Event Severity", self.get("severity"), "severity") if self.get("seriousness") else "",
			"outcome": get_code_list("Adverse Event Outcome", self.get("outcome"), "outcome") if self.get("outcome") else "",
			"participant": get_participant(self.get("participants")) if self.get("participants") else "",
			"recorder": get_reference(self.get("recorder_type"), self.get("recorder")) if self.get("recorder") else "",
			# "contributor": get_optional_doctype(self.get("contributor_type"), self.get("contributor")),
			# "suspectEntity": [self.get_suspect_entity(suspect_entity) for suspect_entity in self.suspect_entity] if self.get("suspect_entity") else "",
			# "subjectMedicalHistory": get_optional_doctype(self.get("subject_medical_history_type"), self.get("subject_medical_history")),
			# "referenceDocument": get_reference("Reference Document", self.reference_document.split("-")[2]) if self.get("reference_document") else "",
			# "study": get_reference("Study", self.study.split("-")[2]) if self.get("study") else "",
			# "note": [
			# 	{
			# 		"text": single_note.get("text")
			# 	} for single_note in self.get("note")
			# ] if self.get("note") else "",
		}
		print(fhir_schema)
		return fhir_schema
	
	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()
			
			response = requests.post(
					lafia_base_url + '/fhir/AdverseEvent',
					json=fhir_schema, verify=False)
			
			event_object = response.json()
			frappe.errprint(event_object)
		
			if event_object.get("status") == 201:
				self.fhir_serverid = event_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")

	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/AdverseEvent/' + self.fhir_serverid,
			json=fhir_schema, verify=False)
			
		event_object = response.json()
		print(event_object)

	
	def on_trash(self):
		response = requests.delete(
			lafia_base_url + '/fhir/AdverseEvent/' + self.fhir_serverid, verify=False)		
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type" : "adverse event",
			"resource_id": self.fhir_serverid,
			"data" : {
			}

		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	# def get_suspect_entity(self, suspect_entity):
	# 	suspect_entity_dict = {
	# 		"instance": get_optional_doctype(self.get("instance_type"), self.get("instance")),
	# 		"causality": [{
	# 			"coding": [get_code("Adverse Event Causality", suspect_entity.get("causality"))] if suspect_entity.get("causality") else []
	# 			}],
			
	# 	}
	# 	return suspect_entity_dict

def get_participant(participants):
	participant_list = []
	for part in participants:
		participant_list.append({
			"actor": get_reference(part.get("participant_role"),part.get("participant")),
			"function": {
				"coding": [get_code("Participant Type", part.get("function"))]
				} if part.get("function") else ""
		})
	return participant_list