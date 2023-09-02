# Copyright (c) 2023, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os, json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_reference,format_datetime,get_code_list
from lafia.api.services.brokers.producer import producer
from frappe.utils import get_date_str, get_site_name
from dotenv import load_dotenv

load_dotenv()
lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class VerificationResult(Document):
	
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "VerificationResult",
			"target": [get_reference(self.target_resource,self.target)],
			"targetLocation": [self.target_location],
			"need": {"text":self.need} if self.need else "",
			"status": (self.status).lower(),
			"statusDate": format_datetime(self.status_date) if self.status_date else "",
			"validationType": {"text":self.validation_type} if self.validation_type else "",
			"validationProcess": get_code_list("Verification Process", self.get("validation_process"), "verification_process") if self.get("validation_process") else []
		}
		print(fhir_schema)
		return fhir_schema
	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/VerificationResult', json=fhir_schema)
			
			ver_object = response.json()
			frappe.errprint(ver_object)

			if response.status_code == 201:
				self.fhir_serverid = ver_object["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/VerificationResult/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		ver_object = response.json()
		print(ver_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/VerificationResult/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "VerificationResult",
        	"resource_id": self.fhir_serverid,
			"data": {
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))
