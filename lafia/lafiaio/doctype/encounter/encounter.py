# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os
from frappe.model.document import Document
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier, get_code, get_period

load_dotenv()


lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Encounter(Document):

	def get_body(self):

		fhir_schema = {
				"resourceType": "Encounter",
				"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
				"status": self.get("status"),
				"class": self.get_class(self.get("class")) if self.get("class") else "",
				"subject": self.get_subject(self.subject) if self.get("subject") and self.get("subject_type") else "",
				"participant": self.get_participants(self.participants) if self.get("participants") else "",
				"type": [
					{
						"coding": [get_code("Encounter Type Code", self.get("type"))]
					}
				] if self.get("type") else "",
				"period": get_period(self.period) if self.get("period") else ""
		}
		return fhir_schema

	def before_save(self):
		fhir_schema = self.get("get_body")()
		response = requests.put(
				'{0}/fhir/Encounter/{1}'.format(lafia_base_url, self.get("fhir_serverid")), json=fhir_schema)
		print(response.status_code)
		if not response.status_code == 200:
			print(response.__dict__)
			frappe.throw("An error occured")

	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.get_body()
			response = requests.post(
					lafia_base_url + '/fhir/Encounter', json=fhir_schema)
			if not response.status_code == 201:
					frappe.throw("An error occured")
			else:
					encounter_fhir_object = response.json()
					self.fhir_serverid = encounter_fhir_object.get("id")

	def get_participants(self, participants):
		participant_list = []
		for participant in participants:
			participant_doc = None
			if participant.get("individual_type") == "Practitioner":
				participant_doc = frappe.get_doc("Practitioner", participant.get("individual"))
			obj = {
				"type": [
					{
						"coding": [self.get_code("Participant Type Code", participant.get("type"))]
					}
				],
				"individual": {
					"reference": participant.get("individual_type") + "/" + participant_doc.get("fhir_serverid")
				},
				"period": get_period([{
					"start": participant.get("from_period"),
					"end": participant.get("to_period")
				}])
			}
			participant_list.append(obj)
		return participant_list
	
	def get_class(self, class_display):
		class_doc = frappe.get_doc("Encounter Class Code", class_display)
		return {
			"system": class_doc.get("system"),
			"code": class_doc.get("code"),
			"display": class_doc.get("display")
		}

	def get_subject(self, subject):
		reference = None
		if self.subject_type == "Patient_LafiaIO":
			patient_doc = frappe.get_doc("Patient_LafiaIO", subject)
			reference = "Patient/" + patient_doc.get("fhir_serverid")
		return {
			"reference": reference
		}
