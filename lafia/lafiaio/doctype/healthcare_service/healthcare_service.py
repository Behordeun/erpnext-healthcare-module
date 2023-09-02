# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.document import Document
import sys
import requests
import json
import os, frappe
from frappe import whitelist
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier,get_code_list,get_telecom,get_addresses,get_code,get_reference,get_reference_list,format_datetime
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class HealthcareService(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "HealthcareService",
			"identifier": get_identifier(self.get("identifier")) if self.get("identifier") else [],
			"active": True if self.active == 1 else False,
			"name": self.name1,
			"providedBy": get_reference("Organization",self.provider) if self.provider else "",
			"category": get_code_list("Healthcare Service Category", self.get("category"), "category") if self.get("category") else "",
			"type": get_code_list("Healthcare Service Type", self.get("type"), "service_type") if self.get("type") else "",
			"specialty": get_code_list("Healthcare Service Specialty", self.get("specialty"), "specialty") if self.get("specialty") else "",
			"location": get_reference_list("Locations",self.location,"location") if self.location else "",
			"comment": self.comment,
			"telecom": get_telecom(self.get("email"), self.get("phone")),
			"coverageArea": get_reference_list("Locations",self.coveragearea,"location") if self.coveragearea else "",
			"serviceProvisionCode": get_code_list("Healthcare Service Provision", self.get("serviceprovisioncode"), "service_provision") if self.get("serviceprovisioncode") else "",
			"program": get_code_list("Healthcare Service Program", self.get("program"), "service_program") if self.get("program") else "",
			"characteristic": get_code_list("Healthcare Service Characteristics", self.get("characteristic"), "service_char") if self.get("characteristic") else "",
			"communication": get_code_list("Language Code", self.get("communication"), "language") if self.get("communication") else "",
			"referralMethod": [{"text":self.referralmethod}] if self.referralmethod else "",
			"appointmentRequired": True if self.appointmentrequired == 1 else False,
			"availableTime": self.hours_of_operation() if self.get('availabletime') else "",
			"notAvailable": self.unavailability(),
			"endpoint": get_reference_list("Endpoint",self.endpoint,"endpoint") if self.endpoint else "",
		}
		return fhir_schema

	def hours_of_operation(self):
		operation_list = []
		for operation in self.get('availabletime'):
			operation_list.append({
				"daysOfWeek": [operation.get('weeks')],
				"allDay": True if operation.get('days') == 1 else False,
				"openingTime": get_time_str(operation.get('openingtime')) if operation.get('openingtime') else '',
				"closingTime": get_time_str(operation.get('closingtime')) if operation.get('closingtime') else '',
			})
		return operation_list

	def unavailability(self):
		operation_list = []
		for operation in self.get("notavailable"):
			operation_list.append({
				"description": operation.get("description"),
				"during": {
					"start": format_datetime(operation.get("start")),
					"end": format_datetime(operation.get("end"))
				}
			})
		return operation_list
	

	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/HealthcareService',
				json=fhir_schema, verify=False)
		
			service_object = response.json()
			frappe.errprint(service_object)
		
			if service_object.get("status") == 201:
				self.fhir_serverid = service_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/HealthcareService/' + self.fhir_serverid,
			json=fhir_schema, verify=False)
			
		service_object = response.json()
		print(service_object)

	def after_insert(self):
		event_body = {
			"resource_type": "Healthcare Service",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.name1,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def on_trash(self):
		response = requests.delete(
			lafia_base_url + '/fhir/HealthcareService/' + self.fhir_serverid, verify=False)		
		print(response.json())


