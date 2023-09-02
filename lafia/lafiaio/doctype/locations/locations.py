# Copyright (c) 2022, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.document import Document
import sys
import requests
import json
import os, frappe
from frappe import whitelist
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier,get_code_list,get_telecom,get_addresses,get_code,get_reference
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Locations(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Location",
			"identifier": get_identifier(self.get("identifier")) if self.get("identifier") else [],
			"status": self.status,
			"name": self.namefhir,
			"alias": [self.alias],
			"description": self.description,
			"mode": self.mode,
			"type": get_code_list("Location Role Type", self.get("type"), "location_type") if self.get("type") else "",
			"telecom": get_telecom(self.get("email"), self.get("phone")),
			"address": get_addresses(self.get("address")) if self.address else "",
			"partOf": {"coding": [get_code("Location", self.get("partof"))]} if self.get("partof") else "",
			"physicalType": {"coding": [get_code("Location Type", self.get("physical_type"))]} if self.get("physical_type") else "",
			"position":{'longitude':self.longitude,'latitude':self.latitude,'altitude':self.altitude},
			"managingOrganization": get_reference("Organization",self.organization) if self.organization else "",
			"hoursOfOperation": self.hours_of_operation(),
			"availabilityExceptions" : self.avail,
			"endpoint": get_reference("Endpoint",self.endpoint) if self.endpoint else ""
		}
		return fhir_schema

	def hours_of_operation(self):
		operation_list = []
		for operation in self.get('hoursofoperation'):
			operation_list.append({
				"daysOfWeek": [operation.get('weeks')],
				"allDay": True if operation.get('days') == 1 else False,
				"openingTime": get_time_str(operation.get('openingtime')) if operation.get('openingtime') else '',
				"closingTime": get_time_str(operation.get('closingtime')) if operation.get('closingtime') else '',
			})
		return operation_list

	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/Location',
				json=fhir_schema, verify=False)
		
			location_object = response.json()
			frappe.errprint(location_object)
		
			if location_object.get("status") == 201:
				self.fhir_serverid = location_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/Location/' + self.fhir_serverid,
			json=fhir_schema, verify=False)
			
		location_object = response.json()
		print(location_object)

	def after_insert(self):
		event_body = {
			"resource_type": "Location",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.namefhir,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def on_trash(self):
		response = requests.delete(
			lafia_base_url + '/fhir/Location/' + self.fhir_serverid, verify=False)		
		print(response.json())

