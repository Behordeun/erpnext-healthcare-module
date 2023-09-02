# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os
from frappe.model.document import Document
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier, get_code, get_code_list, get_period, get_reference, get_optional_doctype, get_reference_list,format_datetime,get_practitioner
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


class ClinicalImpression(Document):

	def get_body(self):
		fhir_schema = {
				"resourceType": "ClinicalImpression",
				"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
				"status": (self.get("status")).lower(),
				"statusReason": {
					"coding": [get_code("Clinical Impression Status Reason", self.get("statusreason"))]
				} if self.get("statusreason") else "",
				"description": self.get("description"),
				"subject": get_reference(self.get("subject_type"), self.get("subject")),
				"encounter": get_reference("Patient Encounter", self.encounter) if self.get("encounter") else "",
				"effectiveDateTime": format_datetime(self.effectivedatetime) if self.get("effectivedatetime") else "",
				# "effectivePeriod": get_period(self.effective_period) if self.get("effective_period") else "",
				"date": format_datetime(self.date) if self.get("date") else "",
				"performer": get_practitioner(self.performer) if self.get("performer") else "",
				"previous": get_reference("ClinicalImpression", self.previous) if self.get("previous") else "",
				"problem": self.problem_table() if self.get("problem") else "",
				"changePattern": {"text": self.change},
				# "investigation": [self.get_investigation(investigation) for investigation in self.investigation] if self.get("investigation") else "",
				"protocol": [(self.get("protocol")).lower()],
				"summary": self.get("summary"),
				"finding": self.get_finding() if self.get("investigation") else "",
				"prognosisCodeableConcept": get_code_list("Clinical Impression Prognosis", self.get("prognosiscodeableconcept"), "prognosiscodeableconcept") if self.get("prognosiscodeableconcept") else "",
				"prognosisReference": get_reference_list("RiskAssessment", self.get("prognosisreference"), "riskassessment") if self.get("prognosisreference") else "",
				"supportingInfo": [get_optional_doctype(info.get("link_doctype"), info.get("link_name")) for info in self.get("supportinginfo")] if self.get("supportinginfo") else "",
				# "note": [
				# 	{
				# 		"text": single_note.get("text")
				# 	} for single_note in self.get("note")
				# ] if self.get("note") else ""
		}
		return fhir_schema

	def problem_table(self):
		problem_list = []
		for problem in self.get('problem'):
			problem_list.append(
				get_reference(problem.get('problem_type'),problem.get('problem'))
			)
		return problem_list



	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/ClinicalImpression', json=fhir_schema, verify=False)
			
			clinic_objectt = response.json()
			frappe.errprint(clinic_objectt)

			if clinic_objectt.get("status") == 201:
				self.fhir_serverid = clinic_objectt.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/ClinicalImpression/{0}'.format(self.fhir_serverid),
			json=fhir_schema, verify=False)
			
		clinic_objectt = response.json()
		print(clinic_objectt)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/fhir/ClinicalImpression/' + self.fhir_serverid, verify=False)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "ClinicalImpression",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.subject,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def get_investigation(self, investigation):
		investigation_dict = {
			"code": {
				"coding": [get_code("Investigation Type", investigation.get("code"))] if investigation.get("code") else []
				},
			"item": get_optional_doctype(investigation.get("item_type"), investigation.get("item")) if investigation.get("item") else "",
		}
		return investigation_dict

	def get_finding(self, finding):
		finding_table = []
		for finding in self.get('investigation'):
			finding_table.append(
				{
			# "itemCodeableConcept": {
			# 	"coding": [get_code("Condition Code", finding.get("itemcodeableconcept"))] if finding.get("itemcodeableconcept") else []
			# 	},
			"item": get_reference(finding.get("item_type"), finding.get("item")) if finding.get("item") else "",
			"basis": finding.get("basis")
				}
			)
		
		return finding_table
