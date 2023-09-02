# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
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
from lafia.utils.fhir_utils import get_identifier, get_code,get_coms, get_telecom, retrieve_addresses,get_addresses
from lafia.api.users.users import sign_up
from frappe.utils import get_site_name


load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


class Organization(Document):
	
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Organization",
			"id": self.uid,
			"identifier": get_identifier(self.get("identifier")) if self.get("identifier") else [],
			"active": True if self.active == 1 else False,
			"type": [{"coding": [get_code("Organization Type", self.get("type"))]}] if self.get("type") else "",
			"name": self.name1,
			"alias": [self.alias],
			"telecom": get_telecom(self.get("email"), self.get("phone")),
			"address": get_addresses(self.get("address")) if self.address else "",
			"partOf": self.partof
		}
		print(fhir_schema)
		return fhir_schema
	
		
	
	# def before_insert(self):
	# 	if not self.fhir_serverid:
	# 		print(self.__dict__)
	# 		fhir_schema = self.fhir_object()
			
	# 		response = requests.post(
	# 			lafia_base_url + '/Organization',
	# 			json=fhir_schema)
		
	# 		org_object = response.json()
	# 		frappe.errprint(org_object)
		
	# 		if response.status_code == 201:
	# 			self.fhir_serverid = org_object.get("id")
		
	# 		else:
	# 			frappe.throw("An error occured")
	
	# def on_update(self):
	# 	fhir_schema = self.fhir_object()
	# 	fhir_schema["id"] = self.fhir_serverid

	# 	response = requests.put(
    #         lafia_base_url + '/Organization/' + self.fhir_serverid,
	# 		json=fhir_schema)
			
	# 	org_object = response.json()
	# 	print(org_object)

	# def after_insert(self):
	# 	event_body = {
	# 		"resource_type": "Organization",
    #     	"resource_id": self.fhir_serverid,
	# 		"data": {
	# 			"name": self.name1,
	# 			"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
	# 			"id": self.fhir_serverid
	# 		}
	# 	}
	# 	producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	# def on_trash(self):
	# 	response = requests.delete(
	# 		lafia_base_url + '/Organization/' + self.fhir_serverid)		
	# 	print(response.json())



def get_org_doc(data):
	response = requests.get(
    lafia_base_url + '/Organization/' + data.get("id"))
	doc = response.json()
	print(doc)
	fhir_data = {
		"id": doc["id"],
		"type": doc["type"],
		"active": doc["active"],
		"name": doc["name"],
		"alias": doc["alias"],
		# "telecom": doc["telecom"],
		# "address": doc["address"]
	}
	create_organization(fhir_data)

@whitelist(allow_guest=True)
def create_organization(org_data):
	org_doc_data = {
		"doctype": "Organization",
		"name1": org_data.get("name"),
		"alias": org_data.get("alias")[0] if org_data.get('alias') else '',
		"active": 1 if org_data.get("active") == "true" else 0,
		"type": org_data.get("type")[0].get("coding")[0].get("display") if org_data.get("type") else "",
		"fhir_serverid": org_data.get("id")
		# "phone": get_coms("phone", org_data.get("telecom")),
		# "email": get_coms("email", org_data.get("telecom")),
		# "address": retrieve_addresses(org_data.get("address"))
	}
	org_doc = frappe.get_doc(org_doc_data)
	org_doc.insert()
	frappe.db.commit()
	return org_doc