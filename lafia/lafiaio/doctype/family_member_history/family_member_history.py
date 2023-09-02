# Copyright (c) 2022, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe,json,os
from frappe import _
from frappe.model.document import Document
import frappe, requests, os
from lafia.utils.fhir_utils import get_identifier, get_code_list, get_reference, get_period, get_optional_doctype, get_reference_list, get_code,format_datetime
from frappe.utils import cint, cstr, getdate,get_date_str
import dateutil
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer
from dotenv import load_dotenv

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class FamilyMemberHistory(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "FamilyMemberHistory",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
			"status": (self.get("status")).lower(),
			"dataAbsentReason": get_code_list("FamilyHistory Absent Reason", self.get("absent_reason"), "dataAbsentReason") if self.get("dabsent_reason") else "",
			"patient": get_reference("Patient", self.patient) if self.get("patient") else "",
			"date": format_datetime(self.date) if self.get("date") else "",
			"name": self.get("member_name"),
			"relationship": {"coding": [get_code("Relationship Code", self.get("relationship"))]} if self.get("relationship") else "",
			"sex": self.sex if self.get("sex") else "",
			# "bornPeriod": get_period(self.get("born_period")),
			"bornDate": self.get("born_date"),
			# "bornString": self.get("born_string"),
			# "ageAge": self.get("age"),
			# "ageRange": self.get("age_range"),
			"ageString": self.get("age"),
			# "estimatedAge": self.get("estimated_age"),
			"deceasedBoolean": True if self.get("deceased_boolean") == 1 else False,
			# "deceasedAge": self.get("deceased_age"),
			# "deceasedRange": self.get("deceased_range"),
			"deceasedDate": get_date_str(self.get("deceased_date")) if self.get("deceased_date") else '',
			# "deceasedString": self.get("deceased_string"),
			"reason": get_code_list("Clinical Findings", self.get("reason_code"), "clinical_findings") if self.get("reason_code") else "",
			# "reasonReference": get_optional_doctype(self.get("reason_reference_type"), self.get("reason_reference")),
			# "note": [
			# 	{
			# 		"text": single_note.get("text")
			# 	} for single_note in self.get("note")
			# ] if self.get("note") else "",
			"note": [{'text':self.get('note')}],
			"condition": self.get_condition() if self.get("condition") else "",
			"procedure": self.get_procedure() if self.get('procedure') else ""
		}
		return fhir_schema

	@property
	def age(self):
		if not self.dob:
			return
		dob = getdate(self.dob)
		age = dateutil.relativedelta.relativedelta(getdate(), dob)
		return age

	def get_age(self):
		age = self.age
		if not age:
			return
		age_str = f'{str(age.years)} {_("Year(s)")} {str(age.months)} {_("Month(s)")} {str(age.days)} {_("Day(s)")}'
		return age_str


	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/FamilyMemberHistory', json=fhir_schema, verify=False)
			
			fmh_object = response.json()
			frappe.errprint(fmh_object)

			if fmh_object.get("status") == 201:
				self.fhir_serverid = fmh_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/FamilyMemberHistory/{0}'.format(self.fhir_serverid),
			json=fhir_schema, verify=False)
			
		fmh_object = response.json()
		print(fmh_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/fhir/FamilyMemberHistory/' + self.fhir_serverid, verify=False)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "FamilyMemberHistory",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.patient,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))


	def get_condition(self):
		condition_list = []
		for condition in self.get('condition'):
			condition_list.append(
				{
					"code": [{
						"coding": [get_code("Condition Code", condition.get("code"))] if condition.get("code") else []
						}],
					"outcome": {"text":condition.get('outcome')},
					"contributedToDeath": True if condition.get("contributed_to_death") == 1 else False,
					"onsetString": condition.get("age_condition_first_manifested"),
					
				}
			)
		return condition_list

	
	def get_procedure(self):
		procedure_list = []
		for procedure in self.get('procedure'):
			procedure_list.append(
				{
					"code": [{
						"coding": [get_code("Procedure Code", procedure.get("code"))] if procedure.get("code") else []
						}],
					"outcome": {"text":procedure.get('outcome')},
					"contributedToDeath": True if procedure.get("contributed_to_death") == 1 else False,
					"performedDateTime": format_datetime(procedure.get('performed_date')) if procedure.get('performed_date') else ''
				}
			)
		return procedure_list
