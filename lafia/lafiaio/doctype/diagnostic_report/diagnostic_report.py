# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe, requests, os,json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code_list, get_reference,period, get_optional_doctype, get_reference_list, get_code,format_datetime,get_reference_table
from dotenv import load_dotenv
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class DiagnosticReport(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "DiagnosticReport",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
			"basedOn": get_reference_table(self.based_on) if self.get('based_on') else "",
			"status": (self.get("status")).lower(),
			"category": get_code_list("Diagnostic Report Category", self.get("category"), "category") if self.get("category") else "",
			"code": {"coding": [get_code("Report Code", self.get("code"))]} if self.get("code") else [],
			"subject": get_reference("Patient",self.patient),
			"encounter": get_reference("Patient Encounter",self.get('encounter')) if self.get('encounter') else "",
			"effectivePeriod": period(self.start_date,self.end_date) if self.start_date and self.end_date else "",
			"issued": format_datetime(self.get("issued")) if self.get("issued") else "",
			"performer": get_reference_table(self.get("performer")) if self.get("performer") else "",
			"resultsInterpreter": get_reference_table(self.get("result_interpreter")) if self.get("result_interpreter") else "",
			"specimen": get_reference_list("Specimen",self.get('specimen'),'specimen') if self.get('specimen') else "",
			"result": get_reference_list("Observation",self.get('result'),'observation') if self.get('result') else "",
			"note": {"text":self.get("note")},
			"study": get_reference_table(self.get("study")) if self.get("study") else "",
			"supportingInfo": self.get_supportInfo() if self.get('supporting_info') else "",
			"media": self.get_media() if self.get("media") else "",
			"conclusion": self.get("conclusion")
		}
		print(fhir_schema)
		return fhir_schema

	
	def get_supportInfo(self):
		info_list = []
		for info in self.get('supporting_info'):
			info_list.append({
				"type": {"text":info.get('type')},
				"reference": get_reference(info.get("reference_type"),info.get("reference"))
			})
		return info_list

	def get_media(self):
		media_list = []
		for media in self.get("media"):
			media_list.append({
				"comment": media.get('comment'),
				"link": get_reference("Document Reference",media.get('link'))
			})
		return media_list


	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/DiagnosticReport', json=fhir_schema, verify=False)
			
			diag_object = response.json()
			frappe.errprint(diag_object)

			if diag_object.get("status") == 201:
				self.fhir_serverid = diag_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/DiagnosticReport/{0}'.format(self.fhir_serverid),
			json=fhir_schema, verify=False)
			
		diag_object = response.json()
		print(diag_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/fhir/DiagnosticReport/' + self.fhir_serverid, verify=False)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "DiagnosticReport",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.patient,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))
