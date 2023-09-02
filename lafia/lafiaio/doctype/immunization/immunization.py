# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os,json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code, get_reference, get_code_list,\
	format_datetime,get_reference_list,get_practitioner,get_annotation,get_reference_table,get_ratio
from lafia.api.services.brokers.producer import producer
from frappe.utils import get_site_name
from dotenv import load_dotenv
load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Immunization(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "Immunization",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else [],
			"status": (self.status).lower(),
			"patient": self.patient,
			"statusReason": {"coding": [get_code("Immunization Status Reason", self.get("status_reason"))]} if self.get("status_reason") else "",
			"encounter": get_reference("Patient Encounter",self.encounter) if self.encounter else "",
			"occurrenceDateTime": format_datetime(self.occurrence) if self.occurrence else ""
		}
		frappe.errprint(fhir_schema)
		return fhir_schema


	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/Immunization', json=fhir_schema)
			
			immunization_object = response.json()
			frappe.errprint(immunization_object)

			if response.status_code == 201:
				self.fhir_serverid = immunization_object.get("id")
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/Immunization/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		immunization_object = response.json()
		print(immunization_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/Immunization/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "Immunization",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.patient,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

