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

class Medication(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "Medication",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else [],
			"status": (self.status).lower(),
			"code": {"coding": [get_code("Medication Code", self.get("code"))]} if self.get("code") else "",
			"manufacturer": get_reference("Organization",self.get("manufacturer")) if self.get("manufacturer") else "",
			"form": {"coding": [get_code("Medication Form", self.get("form"))]} if self.get("form") else "",
			"ingredient": self.get_ingredient() if self.get("ingredient") else [],
			"batch": {
				"lotNumber":self.lot_number,
				"expirationDate":format_datetime(self.expiration_date) if self.expiration_date else ""
				}
		}
		frappe.errprint(fhir_schema)
		return fhir_schema

	def get_ingredient(self):
		ingredient_list = []
		for ingredient in self.get("ingredient"):
			ingredient_list.append({
				"itemReference": get_reference("Medication",ingredient.get("item_reference")),
				"isActive": True if ingredient.get("is_active") else False,
				"strength": get_ratio(ingredient.get("strength"),ingredient.get("per"))
			})
		return ingredient_list
	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/Medication', json=fhir_schema)
			
			medication_object = response.json()
			frappe.errprint(medication_object)

			if response.status_code == 201:
				self.fhir_serverid = medication_object.get("id")
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/Medication/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		medication_object = response.json()
		print(medication_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/Medication/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "Medication",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.name,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))


