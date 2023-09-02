# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code_list, get_reference,period, get_optional_doctype, get_reference_list, get_code,format_datetime,get_reference_table
from dotenv import load_dotenv
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer
import frappe, requests, os,json

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class BodyStructure(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "BodyStructure",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
			"active": True if self.status == "Active" else False,
			"morphology": {"coding": [get_code("Body Structure Code", self.get("morphology"))]} if self.get("morphology") else [],
			"includedStructure": get_location(self.get("included_structure")) if self.get("included_structure") else [],
			"excludedStructure": get_location(self.get("excluded_structure")) if self.get("excluded_structure") else [],
			"description": self.get("description"),
			"image": [{"url":self.get("image")}],
			"patient": get_reference("Patient",self.get("patient"))
		}
		print(fhir_schema)
		return fhir_schema


	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/BodyStructure', json=fhir_schema, verify=False)
			
			struc_object = response.json()
			frappe.errprint(struc_object)

			if struc_object.get("status") == 201:
				self.fhir_serverid = struc_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/BodyStructure/{0}'.format(self.fhir_serverid),
			json=fhir_schema, verify=False)
			
		struc_object = response.json()
		print(struc_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/fhir/BodyStructure/' + self.fhir_serverid, verify=False)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "BodyStructure",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.patient,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))





def get_location(locations):
	location_list = []
	for location in locations:
		location_list.append({
			"structure": {"coding": [get_code("Body Site Code", location.get("structure"))]} if location.get("structure") else "",
			"laterality": {"text":location.get("laterality")},
			"qualifier": {"text":location.get("qualifier")}
		})
	return location_list
