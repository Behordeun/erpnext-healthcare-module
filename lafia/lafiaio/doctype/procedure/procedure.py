# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, requests, os, json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code, get_code_list, get_reference, get_optional_doctype, get_reference_list, get_encounter, period
from dotenv import load_dotenv
from frappe import whitelist
from lafia.api.services.brokers.producer import producer
from lafia.api.users.users import sign_up
from frappe.utils import get_site_name

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Procedure(Document):

	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Procedure",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
			"basedOn": [get_reference(self.get("basedon_type"), self.get("basedon"))],
			"partOf": [get_reference(self.get("partof_type"), self.get("partof"))],
			"statusReason":  {
				"coding": [get_code("Procedure Not Performed Reason Code", self.get("statusreason"))]
				} if self.get("statusreason") else "",
			"status": self.get("status"),
			"category": {
				"coding": [get_code("Procedure Category Code", self.get("category"))]
				} if self.get("category") else "",
			"code": {
					"coding": [get_code("Procedure Code", self.get("code"))]
				} if  self.get("code") else "",
			"subject": get_reference("Patient", self.get("subject")),
			"encounter": get_encounter(self.encounter) if self.encounter else "",
			# "performedDateTime": self.performeddatetime.replace(" ", "T") if self.get("performeddatetime") else "",
			"performedPeriod": period(self.start,self.stop),
			# "performedString": self.get("performedstring"),
			"asserter": get_optional_doctype(self.asserter_type, self.asserter),
			"recorder": get_optional_doctype(self.recorder_type, self.recorder),
			"performer": self.get_performer(self.performer) if self.get("performer") else "",
			"location": get_reference("Location FHIR", self.location) if self.location else "",
			"reasonCode": get_code_list("Procedure Reason Code Multi", self.get("reasoncode"), "procedure_reason_code") if self.get("reasoncode") else "",
			"bodySite": get_code_list("Body Site Multi", self.get("bodysite"), "body_site_code") if self.get("bodysite") else "",
			"reasonReference": [get_optional_doctype(self.reason_reference_type, self.reason_reference)] if self.get("reason_reference") else "",
			"outcome": {
				"coding": [get_code("Procedure Outcome Code", self.get("outcome"))]
				} if self.get("outcome") else "",
			"report": [get_optional_doctype(report.get("report_type"), report.get("report")) for report in self.get("report")] if self.get("report") else "",
			"complication": get_code_list("Condition Code Multi", self.get("condition"), "condition") if self.get("condition") else "",
			"complicationDetail": get_reference_list("Condition", self.get("complicationdetail"), "condition") if self.get("complicationdetail") else "",
			"followUp": get_code_list("Procedure Followup Code Multi", self.get("followup"), "procedure_followup") if self.get("followup") else "",
			"note": [
				{
					"text": single_note.get("text")
				} for single_note in self.get("note")
			] if self.get("note") else "",
			"usedReference": [get_optional_doctype(reference.get("reference_type"), reference.get("reference")) for reference in self.get("usedreference")] if self.get("usedreference") else ""
			# "class": self.get_class(self.get("class")),

			# "period": get_period(self.period)
		}
		return fhir_schema
	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			response = requests.post(
					lafia_base_url + '/fhir/Procedure', json=fhir_schema)
			if not response.status_code == 201:
					print(response.__dict__)
					frappe.throw("An error occured")
			else:
					procedure_fhir_object = response.json()
					self.fhir_serverid = procedure_fhir_object.get("id")

	def before_save(self):
		fhir_schema = self.fhir_object()
		
		response = requests.put(
				'{0}/fhir/Procedure/{1}'.format(lafia_base_url, self.fhir_serverid), json=fhir_schema)
		if not response.status_code == 200:
			print(response.__dict__)
			frappe.throw("An error occured")



	def after_insert(self):
		event_body = {
			"resource_type": "Procedure",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.name,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))


	def get_performer(self, performers):
		return [
			{
				"function":{
					"coding": [get_code("Procedure Performer Code", performer.get("function"))]
					} if performer.get("function") else "",
				"actor": get_reference(performer.get("actor_type"), performer.get("actor")),
				"onBehalfOf": get_reference("Organization", performer.get("on_behalf_of"))
			} for performer in performers
		]
	

# def get_report(self, reports):
# 	return 
