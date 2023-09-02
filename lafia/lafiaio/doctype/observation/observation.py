# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from frappe.website.website_generator import WebsiteGenerator
import frappe, os, requests, json
from frappe.utils import get_bench_path, get_site_name, now_datetime
from frappe.model.document import Document
from frappe import whitelist
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier,get_code_list,get_code,get_reference,format_datetime,get_reference_table,get_annotation
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


class Observation(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Observation",
			"identifier": get_identifier(self.identifier) if self.identifier else "",
			"status": (self.status).lower(),
			"category": get_code_list("Observation Category Code", self.get("category"), "category") if self.get("category") else "",
			"code": {"coding": [get_code("Observation Code", self.get("code"))]} if self.get("code") else "",
			"subject": get_reference(self.get("subject_type"),self.get("subject")) if self.get("subject") else "",
			"encounter": get_reference("Patient Encounter",self.encounter) if self.encounter else "",
			"effectiveDateTime": format_datetime(self.effective) if self.effective else "",
			"performer": get_reference_table(self.get("performer")) if self.get("performer") else "",
			"basedOn": get_reference_table(self.get("based_on")) if self.get("based_on") else "",
			"partOf": get_reference_table(self.get("part_of")) if self.get("part_of") else "",
			"issued": format_datetime(self.issued) if self.issued else "",
			"valueString": self.value,
			"dataAbsentReason": {"text": self.data_absent_reason},
			"interpretation": [{"coding": [get_code("Observation Interpretation", self.get("interpretation"))]}] if self.get("interpretation") else "",
			"note": get_annotation(self.get("note")) if self.get("note") else "",
			"bodySite": {"coding": [get_code("Body Site Code", self.get("body_site"))]} if self.get("body_site") else "",
			"method": {"coding": [get_code("Observation Method", self.get("method"))]} if self.get("method") else "",
			"specimen": get_reference("Specimen",self.specimen) if self.specimen else "",
			"device": get_reference("Device",self.device) if self.device else "",
			"hasMember": get_reference_table(self.get("has_member")) if self.get("has_member") else "",
			"derivedFrom": get_reference_table(self.get("derived_from")) if self.get("derived_from") else ""
		}
		return fhir_schema

	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/Observation', json=fhir_schema, verify=False)
			
			obsev_object = response.json()
			frappe.errprint(obsev_object)

			if obsev_object.get("status") == 201:
				self.fhir_serverid = obsev_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/Observation/{0}'.format(self.fhir_serverid),
			json=fhir_schema, verify=False)
			
		obsev_object = response.json()
		print(obsev_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/fhir/Observation/' + self.fhir_serverid, verify=False)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "Observation",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.subject,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

