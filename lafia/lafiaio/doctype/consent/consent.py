# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, os, requests, json
from frappe.utils import get_bench_path, get_site_name, now_datetime
from frappe.model.document import Document
from frappe import whitelist
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier,get_code_list,get_telecom,get_addresses,get_code,get_reference,get_reference_list,format_datetime
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


class Consent(Document):

	def log_errors(self, error):
		request_uri = frappe.request.environ.get("PATH_INFO")
		site_name = get_site_name(frappe.request.host)
		error_msg = """
		\n[{0}]: {1}
				PATH: {2}
				MESSAGE: {3}
		""".format(now_datetime(), site_name, request_uri, error)
		log_file = open(get_bench_path() + "/logs/{0}.app-error.log".format(site_name), "a")
		log_file.write(error_msg)
		return error_msg

	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Consent",
			"identifier": get_identifier(self.identifier) if self.identifier else "",
			"status": (self.status).lower(),
			"scope": [{"coding": [get_code("Consent Scope Code", self.get("scope"))]}] if self.get("scope") else "",
			"category": get_code_list("Consent Category Code", self.get("category"), "category_code") if self.get("category") else "",
			"patient": get_reference("Patient",self.patient),
			"performer": get_reference(self.performer_type, self.performer) if self.get("performer") else "",
			"dateTime": format_datetime(self.get("datetime")),
			"organization": [get_reference("Organization",self.organization)] if self.organization else "",
			"sourceReference": get_reference(self.source_ref_type, self.source_ref) if self.source_ref else "",
			"verification": self.verifications() if self.verification else ""
		}
		return fhir_schema

	
	def verifications(self):
		verification_list = []
		for ver in self.verification:
			verification_list.append({
				"verified": True if ver.get("verified") == "Yes" else False,
				"verifiedWith": get_reference(ver.get("verification_ref"),ver.get("verifiedwith")),
				"verificationDate": ver.get("verification_date")
			})
		return verification_list



	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()

			response = requests.post(
				lafia_base_url + '/Consent',
				json=fhir_schema, verify=False)
		
			consent_object = response.json()
			frappe.errprint(consent_object)

			if response.status_code == 201:
				self.fhir_serverid = consent_object.get("id")
		
			else:
				self.log_errors(response.__dict__)
				frappe.throw("An error occured")

	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/Consent/' + self.fhir_serverid,
			json=fhir_schema, verify=False)
			
		consent_object = response.json()
		print(consent_object)

	def after_insert(self):
		event_body = {
			"resource_type": "Consent",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.patient,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def on_trash(self):
		response = requests.delete(
			lafia_base_url + '/Consent/' + self.fhir_serverid, verify=False)		
		print(response.json())


