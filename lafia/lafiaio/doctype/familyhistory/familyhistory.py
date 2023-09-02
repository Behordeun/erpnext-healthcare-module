# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code_list, get_reference, get_period, get_optional_doctype, get_reference_list, get_code
from dotenv import load_dotenv
load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class FamilyHistory(Document):
	def get_body(self):
		fhir_schema = {
				"resourceType": "FamilyHistory",
				"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
				"status": self.get("status"),
				"dataAbsentReason": get_code_list("FamilyHistory Absent Reason", self.get("dataAbsentReason"), "dataAbsentReason") if self.get("dataAbsentReason") else "",
				"patient": get_reference("Patient_LafiaIO", self.patient.split("-")[2]) if self.get("patient") else "",
				"date": self.date.replace(" ", "T") if self.get("date") else "",
				"name": self.get("member_name"),
				"relationship": get_code_list("Relationship Code", self.get("relationship"), "relationship") if self.get("relationship") else "",
				"sex": get_code_list("FamilyHistory Sex Code", self.get("sex"), "sex") if self.get("sex") else "",
				"bornPeriod": get_period(self.get("born_period")),
				"bornDate": self.get("born_date"),
				"bornString": self.get("born_string"),
				"ageAge": self.get("age"),
				"ageRange": self.get("age_range"),
				"ageString": self.get("age_string"),
				"estimatedAge": self.get("estimated_age"),
				"deceasedBoolean": self.get("deceased_boolean"),
				"deceasedAge": self.get("deceased_age"),
				"deceasedRange": self.get("deceased_range"),
				"deceasedDate": self.get("deceased_date"),
				"deceasedString": self.get("deceased_string"),
				"reasonCode": get_code_list("FamilyHistory Reason Code Multi", self.get("reason_code"), "family_history_reason_code") if self.get("reason_code") else "",
				"reasonReference": get_optional_doctype(self.get("reason_reference_type"), self.get("reason_reference")),
				"note": [
					{
						"text": single_note.get("text")
					} for single_note in self.get("note")
				] if self.get("note") else "",
				"condition": [self.get_condition(condition) for condition in self.condition] if self.get("condition") else "",
			}
		return fhir_schema

	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.get_body()
			response = requests.post(
					lafia_base_url + '/fhir/FamilyHistory', json=fhir_schema)
			if not response.status_code == 201:
					print(response.__dict__)
					frappe.throw("An error occured")
			else:
					family_fhir_object = response.json()
					self.fhir_serverid = family_fhir_object.get("id")

	def before_save(self):
		if not self.fhir_serverid:
			fhir_schema = self.get_body()
			response = requests.put(
				'{0}/fhir/FamilyHistory/{1}'.format(lafia_base_url, self.fhir_serverid), json=fhir_schema)
			if not response.status_code == 200:
				print(response.__dict__)
				frappe.throw("An error occured")

	def get_condition(self, condition):
		condition_dict = {
			"code": [{
				"coding": [get_code("FamilyHistory Condition Code", condition.get("code"))] if condition.get("code") else []
				}],
			"outcome": [{
				"coding": [get_code("FamilyHistory Outcome Code", condition.get("outcome"))] if condition.get("outcome") else []
				}],
			"contributedToDeath": condition.get("contributedToDeath"),
			"onsetAge": condition.get("onsetAge"),
			"onsetRange": condition.get("onsetRange"),
			"onsetPeriod": get_period(condition.get("period")) if condition.get("period") else "",
			"onsetString": condition.get("onsetString"),
			
		}
		return condition_dict
