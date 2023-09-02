# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os
from frappe.model.document import Document
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier, get_code, get_code_list, get_reference, get_optional_doctype

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Goal(Document):

	def get_body(self):
		fhir_schema = {
				"resourceType": "Goal",
				"identifier": get_identifier(self.identifier),
				"lifecycleStatus": self.get("life_cycle_status"),
				"category": get_code_list("Goal Category", self.get("category"), "category") if self.get("category") else "",
				"priority": {
					"coding": [get_code("Goal Priority", self.get("priority"))]
				} if self.get("priority") else "",
				"description": {
					"coding": [get_code("Clinical Findings", self.get("description"))]
				} if self.get("description") else "",
				"subject": get_optional_doctype(self.get("subject_type"), self.get("subject")),
				"startDate": self.start_date,
				"target": [self.get_target(one_target) for one_target in self.target] if self.get("target") else "",
				"statusDate": self.status_date,
				"status_reason": self.get("status_reason"),
				"expressedBy": get_optional_doctype(self.get("expressed_by_type"), self.get("expressed_by")),
				"addresses": get_optional_doctype(self.get("addresses_type"), self.get("addresses")) if self.get("addresses") else "",
				"note": [
					{
						"text": single_note.get("text")
					} for single_note in self.get("note")
				] if self.get("note") else "",
				"outcomeCode": get_code_list("Clinical Findings", self.get("outcome_code"), "clinical_findings") if self.get("outcome_code") else "",
				"outcomeReference": get_reference("Observation", self.outcome_reference.split("-")[2]) if self.get("outcome_reference") else ""
				# "class": self.get_class(self.get("class")),

				# "period": get_period(self.period)
		}
		return fhir_schema


	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.get_body()
			response = requests.post(
					lafia_base_url + '/fhir/Goal', json=fhir_schema)
			if not response.status_code == 201:
					print(response.__dict__)
					frappe.throw("An error occured")
			else:
					procedure_fhir_object = response.json()
					self.fhir_serverid = procedure_fhir_object.get("id")

	def before_save(self):
		if not self.fhir_serverid:
			fhir_schema = self.get_body()
			response = requests.put(
					'{0}/fhir/Goal/{1}'.format(lafia_base_url, self.fhir_serverid), json=fhir_schema)
			if not response.status_code == 200:
					print(response.__dict__)
					frappe.throw("An error occured")

	def get_target(self, target):
		target_dict = {
			"measure": {
				"coding": [get_code("Observation Codes", target.get("measure")) if target.get("measure") else ""]
			},
			"detailString": target.get("detail_string"),
			"detailBoolean": target.get("detail_boolean") == 1,
			"detailInteger": target.get("detail_integer") if target.get("detail_integer") else "",
			"dueDate": target.get("due_date")
		}
		return target_dict
