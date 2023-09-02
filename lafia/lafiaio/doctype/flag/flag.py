# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os,json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code, get_reference, get_code_list,format_datetime,get_reference_list,get_practitioner
from lafia.api.services.brokers.producer import producer
from frappe.utils import get_site_name
from dotenv import load_dotenv
load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Flag(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "Flag",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else [],
			"status": (self.status).lower(),
			"category": get_code_list("Flag Category", self.get("category"), "category") if self.get("category") else "",
			"code": {"coding": [get_code("Flag Code", self.get("code"))]},
			"subject": get_reference(self.subject_ref,self.subject),
			"period": {
					"start": format_datetime(self.get("start")),
					"end": format_datetime(self.get("end"))
				},
			"encounter": get_reference("Patient Encounter",self.encounter) if self.encounter else "",
			"author": get_reference(self.author_ref,self.author) if self.author else ""
		}
		print(fhir_schema)
		return fhir_schema

	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/Flag', json=fhir_schema)
			
			flag_object = response.json()
			frappe.errprint(flag_object)

			if response.status_code == 201:
				self.fhir_serverid = flag_object["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/Flag/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		flag_object = response.json()
		print(flag_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/Flag/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "Flag",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.subject,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

