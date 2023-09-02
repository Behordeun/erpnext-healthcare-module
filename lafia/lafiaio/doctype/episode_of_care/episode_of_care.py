# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
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

class EpisodeOfCare(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "EpisodeOfCare",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else [],
			"status": (self.status).lower(),
			"statusHistory": self.get_status_history() if self.get("status_history") else [],
			"type": get_code_list("Episode Of Care Type", self.get("type"), "type") if self.get("type") else "",
			"diagnosis": self.get_diagnosis() if self.get("diagnosis") else [],
			"patient": self.patient,
			"managingOrganization": get_reference("Organization",self.managing_organization) if self.managing_organization else "",
			"period": {
					"start": format_datetime(self.get("start_date")) if self.get("start_date") else "",
					"end": format_datetime(self.get("end_date")) if self.get("end_date") else ""
				},
			"referralRequest": get_reference_list("Service Request",self.get("referral_request"), "service_request") if self.get("referral_request") else [],
			"careManager": get_practitioner(self.practitioner) if self.practitioner else "",
			"team": get_reference_list("CareTeam",self.get("team"),"care_team") if self.get("team") else [],
			"account": [{"display": self.account}] if self.account else []
		}
		print(fhir_schema)
		return fhir_schema


	def get_status_history(self):
		status_list = []
		for status in self.get("status_history"):
			status_list.append({
				"status": (status.get("status")).lower(),
				"period": {
					"start": format_datetime(status.get("start")),
					"end": format_datetime(status.get("end"))
				}
			})
		return status_list
	
	def get_diagnosis(self):
		diagnosis_list = []
		for diagnosis in self.get("diagnosis"):
			diagnosis_list.append({
				"condition": get_reference("Condition", diagnosis.get("condition")),
				"role": {"coding": [get_code("Diagnosis Role", diagnosis.get("role"))]} if diagnosis.get("role") else "",
				"rank": diagnosis.get("rank")
			})
		return diagnosis_list

	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/EpisodeOfCare', json=fhir_schema)
			
			care_object = response.json()
			frappe.errprint(care_object)

			if response.status_code == 201:
				self.fhir_serverid = care_object["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/EpisodeOfCare/{0}'.format(self.fhir_serverid),
			json=fhir_schema)
			
		care_object = response.json()
		print(care_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/EpisodeOfCare/' + self.fhir_serverid)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "EpisodeOfCare",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.patient,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))


