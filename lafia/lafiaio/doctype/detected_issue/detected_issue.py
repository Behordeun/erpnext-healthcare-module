# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os,json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code_list, get_reference, get_period, get_optional_doctype, get_reference_list, get_code,format_datetime,get_reference_table
from dotenv import load_dotenv
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class DetectedIssue(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "DetectedIssue",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
			"status": (self.get("status")).lower(),
			"code": get_code_list("Detected Issue Category Code", self.get("category"), "category") if self.get("category") else "",
			"severity": (self.get("severity")).lower(),
			"dataAbsentReason": get_code_list("FamilyHistory Absent Reason", self.get("dataAbsentReason"), "dataAbsentReason") if self.get("dataAbsentReason") else "",
			"subject": get_reference("Patient", self.patient) if self.get("patient") else "",
			"identifiedDateTime": format_datetime(self.get("identified_datetime")) if self.get("identified_datetime") else "",
			# "identifiedPeriod": get_period(self.get("identified_period")) if self.get("identified_period") else "",
			"author": get_reference(self.get("author_type"), self.get("author")) if self.get("author") else '',
			"implicated": get_reference_table(self.implications) if self.get('implications') else '',
			"evidence": self.get_evidence() if self.get("evidence") else "",
			"detail": self.get("detail"),
			"reference": self.get("reference"),
			"mitigation": self.get_mitigation() if self.get("mitigation") else "",
		}
		print(fhir_schema)
		return fhir_schema


	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/DetectedIssue', json=fhir_schema, verify=False)
			
			detec_object = response.json()
			frappe.errprint(detec_object)

			if detec_object.get("status") == 201:
				self.fhir_serverid = detec_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/DetectedIssue/{0}'.format(self.fhir_serverid),
			json=fhir_schema, verify=False)
			
		detec_object = response.json()
		print(detec_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/fhir/DetectedIssue/' + self.fhir_serverid, verify=False)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "DetectedIssue",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.patient,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))


	def get_evidence(self):
		evidence_list  = []
		for evidence in self.get('evidence'):
			evidence_list.append({
				"code": [{
					"coding": [get_code("Clinical Findings", evidence.get("code"))] if evidence.get("code") else []
					}],
				"detail": get_reference(evidence.get("detail_type"), evidence.get("detail")) if evidence.get("detail") else "",
			})
		return evidence_list


	def get_mitigation(self):
		mitigation_list = []
		for mitigation in self.get('mitigation'):
			mitigation_list.append({
				"action": [{
					"coding": [get_code("Detected Issue Mitigation Action Code", mitigation.get("action"))] if mitigation.get("action") else []
					}],
				"date": format_datetime(mitigation.get("date")) if mitigation.get("date") else "",
				"author": get_reference(mitigation.get("author_type"), mitigation.get("author")) if mitigation.get("author") else "",
			})
		return mitigation_list