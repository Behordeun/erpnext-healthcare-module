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

class Endpoint(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Endpoint",
			"identifier": get_identifier(self.get("identifier")) if self.get("identifier") else [],
			"status": (self.status).lower(),
			"connectionType": get_code_list("Endpoint Connection Type",self.get("connectiontype"),"type") if self.get("connectiontype") else "",
			"name":self.name1,
			"description": self.description,
			"environmentType": get_code_list("Endpoint environment",self.get("environment_type"),"env") if self.get("environment_type") else "",
			"managingOrganization": get_reference("Organization",self.organization) if self.organization else "",
			"contact": get_telecom(self.get("email"), self.get("phone")),
			"period": period(self.start_date,self.end_date) if self.start_date else "",
			"payloadType": get_code_list("Endpoint Payload",self.get("payloadtype"),"payload") if self.get("payloadtype") else "",
			"payloadMimeType": [self.payloadmimetype],
			"address": self.address,
			"header": [self.header]
		}
		print(fhir_schema)
		return fhir_schema


	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/Endpoint',
				json=fhir_schema, verify=False)
		
			end_object = response.json()
			frappe.errprint(end_object)
		
			if end_object.get("status") == 201:
				self.fhir_serverid = end_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/Endpoint/' + self.fhir_serverid,
			json=fhir_schema, verify=False)
			
		end_object = response.json()
		print(end_object)

	def after_insert(self):
		event_body = {
			"resource_type": "Endpoint",
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
			lafia_base_url + '/fhir/Endpoint/' + self.fhir_serverid, verify=False)		
		print(response.json())



