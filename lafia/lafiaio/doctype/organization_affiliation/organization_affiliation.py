# Copyright (c) 2022, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.document import Document
import frappe
import sys
import requests
import json
import os
from dotenv import load_dotenv
from frappe import whitelist
from lafia.api.services.brokers.producer import producer
from lafia.utils.fhir_utils import get_identifier, get_code,period,get_reference,get_reference_list,get_code_list,get_telecom
from lafia.api.users.users import sign_up
from frappe.utils import get_site_name


load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


class OrganizationAffiliation(Document):

	def fhir_object(self):
		fhir_schema = {
			"resourceType": "OrganizationAffiliation",
			"identifier": get_identifier(self.get("identifier")) if self.get("identifier") else [],
			"active": True if self.active == 1 else False,
			"period": period(self.start_date,self.end_date) if self.start_date else "",
			"organization": get_reference("Organization",self.organization) if self.organization else "",
			"participatingOrganization": get_reference("Organization",self.participating_organization) if self.participating_organization else "",
			"network": get_reference_list("Organization",self.network,"organization") if self.network else [],
			"code": get_code_list("Organization Role",self.get("role"),"role") if self.get("role") else "",
			"specialty": get_code_list("Healthcare Service Specialty", self.get("specialty"), "specialty") if self.get("specialty") else "",
			"location": get_reference_list("Locations",self.location,"location") if self.location else "",
			"healthcareService": get_reference_list("Healthcare Service",self.get("healthcare_service"),"service") if self.get("healthcare_service") else "",
			"endpoint": get_reference_list("Endpoint",self.endpoint,"endpoint") if self.endpoint else [],
			"contact": self.get_contact() if self.contact else []
		}
		
		print(fhir_schema)
		return fhir_schema
	
	def get_contact(self):
		contact_list = []
		for cont in self.get('contact'):
			contact_list.append({
				"name": [{"text":cont.get('name1')}],
				"purpose": {'text':cont.get('purpose')},
				"telecom": get_telecom(cont.get("email"), cont.get("phone")),
				"address": {
					"text": cont.get('address'),
					"city": cont.get('city'),
					"country": cont.get('country')
				},
				"organization": get_reference("Organization",cont.get('organization')) if cont.get('organization') else "",
			})
		return contact_list


	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/OrganizationAffiliation',
				json=fhir_schema, verify=False)
		
			org_object = response.json()
			frappe.errprint(org_object)
		
			if org_object.get("status") == 201:
				self.fhir_serverid = org_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/OrganizationAffiliation/' + self.fhir_serverid,
			json=fhir_schema, verify=False)
			
		org_object = response.json()
		print(org_object)

	def after_insert(self):
		event_body = {
			"resource_type": "OrganizationAffiliation",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.organization,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def on_trash(self):
		response = requests.delete(
			lafia_base_url + '/fhir/OrganizationAffiliation/' + self.fhir_serverid, verify=False)		
		print(response.json())
