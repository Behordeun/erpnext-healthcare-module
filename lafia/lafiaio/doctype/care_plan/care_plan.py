# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code_list, get_reference, get_period, get_optional_doctype, get_reference_list

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class CarePlan(Document):

	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = {
				"resourceType": "CarePlan",
				"identifier": get_identifier(self.identifier),
				"basedOn": get_reference_list("Care Plan", self.get("based_on"), "care_plan"),
				"partOf": get_reference_list("Care Plan", self.get("part_of"), "care_plan"),
				"replaces": get_reference_list("CarePlan", self.get("replaces"), "care_plan"),
				"status": self.get("status"),
				"intent": self.get("intent"),
				"category": get_code_list("Care Plan Category", self.get("category"), "category") if self.get("category") else "",
				"title": self.get("title"),
				"description": self.get("description"),
				"subject": get_optional_doctype(self.get("subject_type"), self.get("subject")),
				"encounter": get_reference("Encounter", self.encounter.split("-")[2]) if self.encounter else "",
				"period": get_period(self.get("period")),
				"created": self.created.replace(" ", "T") if self.get("created") else "",
				"author": get_optional_doctype(self.author_type, self.author),
				"contributor": [get_optional_doctype(reference.get("contributor_type"), reference.get("contributor")) for reference in self.get("contributor")] if self.get("contributor") else "",
				"careTeam": get_reference_list("Care Team", self.get("care_team"), "care_team"),
				"addresses": get_reference_list("Condition", self.get("addresses"), "addresses"),
				"supportingInfo": [get_optional_doctype(reference.get("link_doctype"), reference.get("link_name")) for reference in self.get("supporting_info")] if self.get("supporting_info") else "",
				"goal": get_reference_list("Goal", self.get("goal"), "goal") if self.get("goal") else "",
				"note": [
					{
						"text": single_note.get("text")
					} for single_note in self.get("note")
				] if self.get("note") else "",
			}
			response = requests.post(
					lafia_base_url + '/fhir/CarePlan', json=fhir_schema)
			if not response.status_code == 201:
					print(response.__dict__)
					frappe.throw("An error occured")
			else:
					procedure_fhir_object = response.json()
					self.fhir_serverid = procedure_fhir_object.get("id")

# def get_report(self, reports):
# 	return 
