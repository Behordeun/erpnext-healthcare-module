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

class DocumentReference(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "DocumentReference",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
			"basedOn": get_reference_table(self.based_on) if self.get('based_on') else "",
			"status": (self.get("status")).lower(),
			"docStatus": (self.get("doc_status")).lower() if self.get("doc_status") else "",
			"type": {"coding": [get_code("Document Type", self.get("type"))]} if self.get("type") else [],
			"category": get_code_list("Document Category", self.get("category"), "code") if self.get("category") else "",
			"subject": get_reference(self.get('subject_type'),self.get('subject')),
			"context": get_reference_table(self.context) if self.get('context') else "",
			"event": get_code_list("Act Code", self.get("event"), "code") if self.get("event") else "",
			"facilityType": {"coding": [get_code("Facility Type", self.get("facility_type"))]} if self.get("facility_type") else [],
			"practiceSetting": {"coding": [get_code("Healthcare Service Specialty", self.get("practice_setting"))]} if self.get("practice_setting") else [],
			"period": period(self.start_date,self.end_date) if self.start_date and self.end_date else "",
			"date": format_datetime(self.date) if self.date else "",
			"author": get_reference_table(self.authors) if self.get('authors') else "",
			"attester": self.get_attester() if self.get('attester') else [],
			"custodian": get_reference("Organization",self.get("custodian")) if self.get("custodian") else "",
			"relatesTo": self.relates_to() if self.get("relates_to") else [],
			"description": {"text":self.get("description")},
			"securityLabel": get_code_list("Security Label Code", self.get("security_label"), "label") if self.get("security_label") else "",
			"content": self.get_content()
		}
		print(fhir_schema)
		return fhir_schema


	def get_attester(self):
		attester_list = []
		for attester in self.get('attester'):
			attester_list.append({
				"mode": (attester.get('mode')).lower(),
				"time": format_datetime(attester.get('time')) if attester.get('time') else "",
				"party": get_reference(attester.get('party_type'),attester.get('party')) if attester.get('party') else ""
			})
		return attester_list

	def relates_to(self):
		relates_list = []
		for relate in self.get("relates_to"):
			relates_list.append({
				"code": {"text":relate.get('code')},
				"target": get_reference("Document Reference",relate.get('target'))
			})
		return relates_list

	def get_content(self):
		content_list = []
		for content in self.get("content"):
			content_list.append({
				"attachment": {"url": content.get('attachment')}
			})
		return content_list

	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/DocumentReference', json=fhir_schema, verify=False)
			
			doc_object = response.json()
			frappe.errprint(doc_object)

			if doc_object.get("status") == 201:
				self.fhir_serverid = doc_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/DocumentReference/{0}'.format(self.fhir_serverid),
			json=fhir_schema, verify=False)
			
		doc_object = response.json()
		print(doc_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/fhir/DocumentReference/' + self.fhir_serverid, verify=False)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "DocumentReference",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.subject,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

