# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os,json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code, get_reference, get_code_list,format_datetime,get_reference_list,get_contact_detail
from lafia.api.services.brokers.producer import producer
from frappe.utils import get_site_name, get_date_str
from dotenv import load_dotenv
load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class LIbrary(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "Library",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else [],
			"status": (self.status).lower(),
			"version": self.version,
			"tile": self.title,
			"subtitle": self.subtitle,
			"experimental": True if self.experimental else False,
			"type": {"text":self.type},
			"subjectReference": get_reference("Group",self.subject) if self.subject else "",
			"date": format_datetime(self.date) if self.date else "",
			"publisher": self.publisher,
			"contact": [get_contact_detail(self.publisher,self.get("contact"))],
			"description": self.get("description"),
			"jurisdiction": get_code_list("Jurisdiction", self.get("jurisdiction"), "jurisdiction") if self.get("jurisdiction") else "",
			"purpose": self.get("purpose"),
			"usage": self.get("usage"),
			"copyright": self.get("copyright"),
			"approvalDate": get_date_str(self.approval_date) if self.approval_date else "",
			"lastReviewDate": get_date_str(self.last_review_date) if self.last_review_date else "",
			"effectivePeriod": {
				"start": format_datetime(self.get("start")) if self.get("start") else "",
				"end": format_datetime(self.get("end")) if self.get("end") else ""
			},
			"topic": get_code_list("Definition Topic", self.get("topic"), "topic") if self.get("topic") else "",
			"author": [get_contact_detail(self.author,self.get("author_contact"))],
			"editor": [get_contact_detail(self.editor,self.get("editor_contact"))],
			"reviewer": [get_contact_detail(self.reviewer,self.get("reviewer_contact"))],
			"endoser": [get_contact_detail(self.endoser,self.get("endoser_contact"))],

		}
		frappe.errprint(fhir_schema)
		return fhir_schema

	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/Library', json=fhir_schema)
			
			lib_object = response.json()
			frappe.errprint(lib_object)

			if response.status_code == 201:
				self.fhir_serverid = lib_object["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/Library/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		lib_object = response.json()
		print(lib_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/Library/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "Library",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.title,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))


