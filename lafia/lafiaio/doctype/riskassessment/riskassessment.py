# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os
from frappe.model.document import Document
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier, get_code_list, get_reference, get_period, get_optional_doctype, get_reference_list, get_code

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class RiskAssessment(Document):
	def get_body(self):
		fhir_schema = {
				"resourceType": "RiskAssessment",
				"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
				"basedOn": get_reference_list("RiskAssessment", self.get("based_on"), "riskassessment"),
				"parent": get_reference_list("RiskAssessment", self.get("parent1"), "riskassessment"),
				"status": self.get("status"),
				"method": get_code_list("RiskAssessment Method Code", self.get("method"), "method") if self.get("method") else "",
				"code": get_code_list("RiskAssessment Code", self.get("code"), "code") if self.get("code") else "",
				"subject": get_optional_doctype(self.get("subject_type"), self.get("subject")),
				"encounter": get_reference("Encounter", self.encounter.split("-")[2]) if self.get("encounter") else "",
				"occurrenceDateTime": self.get("occurrence_datetime"),
				"occurrencePeriod": get_period(self.get("occurrence_period")),
				"condition": get_reference("Condition", self.condition.split("-")[2]) if self.get("condition") else "",
				"performer": get_optional_doctype(self.get("performer_type"), self.get("performer")),
				"reasonCode": get_code_list("RiskAssessment Reason Code Multi", self.get("reason_code"), "risk_assessment_reason_code") if self.get("reason_code") else "",
				"reasonReference": get_optional_doctype(self.get("reason_reference_type"), self.get("reason_reference")),
				"basis": get_optional_doctype(self.get("basis_type"), self.get("basis")),
				"prediction": [self.get_prediction(prediction) for prediction in self.prediction] if self.get("prediction") else "",
				"mitigation": self.get("mitigation"),
				"note": [
					{
						"text": single_note.get("text")
					} for single_note in self.get("note")
				] if self.get("note") else "",
			}
		return fhir_schema

	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.get_body()
			response = requests.post(
					lafia_base_url + '/fhir/RiskAssessment', json=fhir_schema)
			if not response.status_code == 201:
					print(response.__dict__)
					frappe.throw("An error occured")
			else:
					riskassessment_fhir_object = response.json()
					self.fhir_serverid = riskassessment_fhir_object.get("id")

	def before_save(self):
		if not self.fhir_serverid:
			fhir_schema = self.get_body()
			response = requests.put(
					'{0}/fhir/RiskAssessment/{1}'.format(lafia_base_url, self.fhir_serverid), json=fhir_schema)
			if not response.status_code == 200:
					print(response.__dict__)
					frappe.throw("An error occured")

	def get_prediction(self, prediction):
		prediction_dict = {
			"outcome": [{
				"coding": [get_code("Prediction Outcome Code", prediction.get("outcome"))] if prediction.get("outcome") else []
				}],
			"probabilityDecimal": prediction.get("probabilityDecimal"),
			"probabilityRange": prediction.get("probabilityRange"),
			"qualitativeRisk": [{
				"coding": [get_code("Prediction Qualitative Risk Code", prediction.get("qualitativeRisk"))] if prediction.get("qualitativeRisk") else []
				}],
			"relativeRisk": prediction.get("relativeRisk"),
			"whenPeriod": get_period(prediction.get("period")) if prediction.get("period") else "",
			"whenRange": prediction.get("whenRange"),
			"rationale": prediction.get("rationale")
		}
		return prediction_dict
