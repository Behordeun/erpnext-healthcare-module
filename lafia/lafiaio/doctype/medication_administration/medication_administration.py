# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os,json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code, get_reference, get_code_list,\
	format_datetime,get_reference_list,get_practitioner,get_annotation,get_reference_table
from lafia.api.services.brokers.producer import producer
from frappe.utils import get_site_name
from dotenv import load_dotenv
load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


class MedicationAdministration(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "MedicationAdministration",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else [],
			"partOf": get_reference_table(self.get("part_of")) if self.get("part_of") else [],
			"status": (self.status).lower(),
			"statusReason": get_code_list("Medication Administration Status Reason", self.get("status_reason"), "status_reason") if self.get("status_reason") else "",
			"category": {"text":self.category},
			"medicationReference": get_reference("Medication",self.medication) if self.medication else "",
			"subject": get_reference("Patient",self.patient),
			"context": get_reference("Patient Encounter",self.encounter) if self.encounter else "",
			"supportingInformation": get_reference_table(self.get("supporting_information")) if self.get("supporting_information") else [],
			"effectivePeriod": {
				"start": format_datetime(self.get("start_date")) if self.get("start_date") else "",
				"end": format_datetime(self.get("end_date")) if self.get("end_date") else ""	
			},
			"performer": self.get_performer() if self.get("performer") else [],
			"reasonCode": [{"text":self.reason_code}],
			"reasonReference": get_reference_table(self.get("reason_reference")) if self.get("reason_reference") else [],
			"request": get_reference("Medication Request",self.request) if self.request else "",
			"device": get_reference_list("Device",self.get("device"),"device") if self.get("device") else [],
			"note": get_annotation(self.get("note")) if self.get("note") else [],
		}
		frappe.errprint(fhir_schema)
		return fhir_schema

	
	def get_performer(self):
		performer_list = []
		for performer in self.get("performer"):
			performer_list.append(
				{
					"function":{"text":performer.get("function")},
					"actor": get_reference(performer.get("actor_type"), performer.get("actor"))
				} 
			)
		return performer_list

	def get_dosage(self):
		return {
			"text": self.instructions,
			"site": {"coding": [get_code("Body Site Code", self.get("site"))]} if self.get("site") else "",
			"route": {"coding": [get_code("Exposure Route", self.get("route"))]} if self.get("route") else "",
			"method": {"coding": [get_code("Dosage method", self.get("method"))]} if self.get("method") else "",
			"dose": {"value": self.dose}
		}
	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/MedicationAdministration', json=fhir_schema)
			
			admin_object = response.json()
			frappe.errprint(admin_object)

			if response.status_code == 201:
				self.fhir_serverid = admin_object.get("id")
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/MedicationAdministration/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		admin_object = response.json()
		print(admin_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/MedicationAdministration/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "MedicationAdministration",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.patient,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

			
		
