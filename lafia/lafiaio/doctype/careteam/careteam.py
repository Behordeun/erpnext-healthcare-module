# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os
from frappe.model.document import Document
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier, get_code, get_code_list, get_period, get_reference, get_optional_doctype, get_reference_list, get_telecom

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class CareTeam(Document):

	def get_body(self):
		fhir_schema = {
				"resourceType": "CareTeam",
				"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
				"status": self.get("status"),
				"category": get_code_list("CareTeam Category", self.get("category"), "careteam_category") if self.get("category") else "",
				"name": self.get("name1"),
				"subject": get_optional_doctype(self.get("subject_type"), self.get("subject")),
				"encounter": get_reference("Encounter", self.encounter.split("-")[2]) if self.get("encounter") else "",
				"period": get_period(self.get("period")) if self.get("period") else "",
				"participant": [self.get_participant(participant) for participant in self.participant] if self.get("participant") else "",
				"reasonCode": get_code_list("Clinical Findings", self.get("reasoncode"), "clinical_findings") if self.get("reasoncode") else "",
				"reasonReference": get_reference_list("Condition", self.get("reason_reference"), "condition") if self.get("reason_reference") else [],
				"managingOrganization": get_reference_list("Organization", self.get("managingorganization"), "organization") if self.get("managingorganization") else "",
				"telecom": get_telecom(self.get("telecom")) if self.get("telecom") else "",
				"note": [
					{
						"text": single_note.get("text")
					} for single_note in self.get("note")
				] if self.get("note") else ""
		}
		return fhir_schema

	def before_save(self):
		if self.fhir_serverid and self.name:
			fhir_schema = self.get_body()
			fhir_schema["id"] = self.fhir_serverid
			response = requests.put(
					'{0}/fhir/CareTeam/{1}'.format(lafia_base_url, self.fhir_serverid), json=fhir_schema)
			if not response.status_code == 200:
					print(response.__dict__)
					frappe.throw("An error occured")


	def before_insert(self):
		if not self.get("fhir_serverid"):
			fhir_schema = self.get_body()
			print(fhir_schema)
			response = requests.post(
					lafia_base_url + '/fhir/CareTeam', json=fhir_schema)
			if not response.status_code == 201:
					print(response.__dict__)
					frappe.throw("An error occured")
			else:
					procedure_fhir_object = response.json()
					self.fhir_serverid = procedure_fhir_object.get("id")

	def get_participant(self, participant):
		participant_dict = {
			"role": [{
				"coding": [get_code("Participant Role", participant.get("role"))] if participant.get("role") else []
				}],
			"member": get_optional_doctype(participant.get("member_type"), participant.get("member")) if participant.get("member") else "",
			"onBehalfOf": get_reference("Organization", participant.get("onbehalfof").split("-")[2]) if participant.get("onbehalfof") else "",
			"period": get_period(participant.get("period")) if participant.get("period") else ""
		}
		return participant_dict
