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

class MedicationStatement(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "MedicationStatement",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else [],
			"basedOn": get_reference_table(self.get("basedon")) if self.get("basedon") else [],
			"partOf": get_reference_table(self.get("partof")) if self.get("partof") else [],
			"status": (self.status).lower(),
			"statusReason": get_code_list("Medication Status Reason",self.get("statusreason"),"reason") if self.get("statusreason") else [],
			"category": {"text":self.category},
			"medicationReference": get_reference("Medication",self.medication) if self.medication else "",
			"subject": get_reference("Patient",self.patient),
			"context": get_reference("Patient Encounter",self.encounter) if self.encounter else "",
			"effectiveDateTime": format_datetime(self.date) if self.date else "",
			"informationSource": get_reference(self.informationsource,self.information_source) if self.information_source else "",
			"derivedFrom": get_reference_table(self.get("derivedfrom")) if self.get("derivedfrom") else [],
			"reasonCode": get_code_list("Condition Code",self.get("reasoncode"),"condition") if self.get("reasoncode") else [],
			"reasonReference": get_reference_table(self.get("reasonreference")) if self.get("reasonreference") else [],
			"note": get_annotation(self.get("note")) if self.get("note") else []
		}
		frappe.errprint(fhir_schema)
		return fhir_schema

	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/MedicationStatement', json=fhir_schema)
			
			smt_object = response.json()
			frappe.errprint(smt_object)

			if response.status_code == 201:
				self.fhir_serverid = smt_object.get("id")
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/MedicationStatement/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		smt_object = response.json()
		print(smt_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/MedicationStatement/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "MedicationStatement",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.patient,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

