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
from lafia.utils.fhir_utils import get_identifier,get_code_list,get_telecom,get_addresses,get_code,get_reference,get_reference_list,format_datetime,period
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class PractitionerRole(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "PractitionerRole",
			"identifier": get_identifier(self.get("identifier")) if self.get("identifier") else [],
			"active": True if self.active == 1 else False,
			"period": period(self.start_date,self.end_date) if self.start_date else "",
			"practitioner": get_reference("Healthcare Practitioner",self.practitioner),
			"organization": get_reference("Company",self.organization) if self.organization else "",
			"code": get_code_list("Practitioner Role",self.get("roles"),"role") if self.get("roles") else "",
			"specialty": get_code_list("Healthcare Service Specialty", self.get("specialty"), "specialty") if self.get("specialty") else "",
			"location": get_reference_list("Locations",self.location,"location") if self.location else "",
			"healthcareService": get_reference_list("Healthcare Service",self.get("healthcare_service"),"service") if self.get("healthcare_service") else "",
			"telecom": get_telecom(self.get("email"), self.get("phone")),
			"availableTime": self.hours_of_operation() if self.get('availabletime') else "",
			"notAvailable": self.unavailability(),
			"availabilityExceptions": self.availability_exceptions if self.availability_exceptions else "",
			"endpoint": get_reference_list("Endpoint",self.endpoint,"endpoint") if self.endpoint else [],
		}
		print(fhir_schema)
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
				lafia_base_url + '/PractitionerRole',
				json=fhir_schema)
		
			role_object = response.json()
			# frappe.errprint(role_object)
		
			if response.status_code == 201:
				print("=====Success=====")
				print(response.__dict__)
				self.fhir_serverid = role_object.get("id")
		
			else:
				print("=====Fail=====")
				print(response.__dict__)
				frappe.throw("An error occured")
	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/PractitionerRole/' + self.fhir_serverid,
			json=fhir_schema)
			
		role_object = response.json()
		print(role_object)

	def after_insert(self):
		event_body = {
			"resource_type": "PractitionerRole",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.practitioner_name,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def on_trash(self):
		response = requests.delete(
			lafia_base_url + '/PractitionerRole/' + self.fhir_serverid)		
		print(response.json())

