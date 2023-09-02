# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os,json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code, get_reference, get_code_list,\
	format_datetime,get_reference_list,get_practitioner,get_annotation
from lafia.api.services.brokers.producer import producer
from frappe.utils import get_site_name
from dotenv import load_dotenv
load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class ResourceList(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "List",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else [],
			"status": (self.status).lower(),
			"mode": (self.mode).lower(),
			"title": self.get("title"),
			"code": {"coding": [get_code("List Purpose", self.get("code"))]} if self.get("code") else "",
			"subject": get_reference(self.subject_type,self.subject) if self.subject else "",
			"encounter": get_reference("Patient Encounter",self.encounter) if self.encounter else "",
			"date": format_datetime(self.date) if self.date else "",
			"source": get_reference(self.author_ref,self.author) if self.author else "",
			"orderedBy": {"coding": [get_code("List Order", self.get("order_by"))]} if self.get("order_by") else "",
			"note": get_annotation(self.get("note")) if self.get("note") else "",
			"entry": self.get_entry() if self.get("entry") else []
		}
		print(fhir_schema)
		return fhir_schema

	def get_entry(self):
		entry_list = []
		for entry in self.get("entry"):
			entry_list.append({
				"flag": {"text":entry.get("flag")} if entry.get("flag") else "",
				"deleted": True if entry.get("deleted") == 1 else False,
				"date": format_datetime(entry.get("date")) if entry.get("date") else "",
				"item": get_reference(entry.get("item_type"),entry.get("item")) if entry.get("item") else ""
			})
		return entry_list
	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/List', json=fhir_schema)
			
			list_object = response.json()
			frappe.errprint(list_object)

			if response.status_code == 201:
				self.fhir_serverid = list_object.get("id")
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/List/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		list_object = response.json()
		print(list_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/List/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "List",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.title,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

