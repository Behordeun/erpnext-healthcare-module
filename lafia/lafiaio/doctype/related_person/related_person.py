# Copyright (c) 2022, ParallelScore and contributors
# For license information, please see license.txt

from urllib import response
from frappe.model.document import Document
import frappe
import ssl
import certifi
from frappe.utils import get_site_name,getdate,get_date_str
from pprint import pprint
import sys
import requests
import json
import os
from dotenv import load_dotenv
from lafia.api.services.brokers.producer import producer
from lafia.utils.fhir_utils import get_identifier, get_period, get_telecom, get_fullname,get_addresses,get_reference,get_code
from lafia.api.users.users import sign_up

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


class RelatedPerson(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "RelatedPerson",
			"identifier": get_identifier(self.get("identifier")) if self.get("identifier") else [],
        	"active": True if self.status == "Active" else False,
			"patient": get_reference("Patient",self.related_to),
			"relationship": [{"coding": [get_code("Related Person Relationship", self.get("relationship"))]}] if self.get("relationship") else "",
        	"name": get_fullname(self.first_name, self.last_name, self.middle_name),
        	"telecom": get_telecom(self.get("email"), self.get("phone")),
        	"gender": self.gender.lower(),
        	"birthDate": get_date_str(self.dob) if self.dob else "",
			"address": get_addresses(self.get("address")) if self.address else "",
			"communication": [{
				"language": {"coding": [get_code("Language Code", self.get("language"))]} if self.get("language") else "",
			}]
		}
		return fhir_schema

	
	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/RelatedPerson',
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
            lafia_base_url + '/fhir/RelatedPerson/' + self.fhir_serverid,
			json=fhir_schema, verify=False)
			
		location_object = response.json()
		print(location_object)

	def after_insert(self):
		event_body = {
			"resource_type": "RelatedPerson",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.first_name,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def on_trash(self):
		response = requests.delete(
			lafia_base_url + '/fhir/RelatedPerson/' + self.fhir_serverid, verify=False)		
		print(response.json())


