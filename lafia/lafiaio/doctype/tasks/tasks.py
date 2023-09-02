# Copyright (c) 2022, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, os, requests, json
from frappe.utils import get_bench_path, get_site_name, now_datetime
from frappe.model.document import Document
from frappe import whitelist
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier,get_code_list,get_telecom,get_addresses,get_code,get_reference,get_reference_list,format_datetime,get_reference_table
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Tasks(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Task",
			"identifier": get_identifier(self.identifier) if self.identifier else "",
			"basedOn": get_reference_table(self.get("based_on")) if self.get("based_on") else "",
			"groupIdentifier": get_identifier(self.group_identifier) if self.group_identifier else "",
			"partOf": get_reference_table(self.get("part_of")) if self.get("part_of") else "",
			"status": (self.status).lower(),
			"intent": (self.intent).lower(),
			"priority": (self.priority).lower(),
			"code": [{"coding": [get_code("Task Type Code", self.get("type"))]}] if self.get("type") else "",
			"description": self.description,
			"for": get_reference(self.beneficiary_ref, self.beneficiary) if self.get("beneficiary") else "",
			"encounter": get_reference("Patient Encounter",self.encounter) if self.encounter else "",
			"executionPeriod": {
				"start":format_datetime(self.start),
				"end": format_datetime(self.end)
				},
			"authoredOn": format_datetime(self.creation_date),
			"requester": get_reference(self.requester_ref, self.requester) if self.get("requester") else "",
			"performerType": get_code_list("Performer Type", self.get("performer_type"), "performer") if self.get("category") else "",
			"location": get_reference("Locations",self.get("location")) if self.get("location") else "",
			"reasonCode": {"text":self.reason},
			"insurance": [get_reference("Coverage", self.get("insurance"))] if self.get("insurance") else "",
			"owner": get_reference(self.owner_ref,self.owner1) if self.owner1 else ""
		}
		print(fhir_schema)
		return fhir_schema

	def before_insert(self):
		if not self.fhir_serverid:
			print(self.__dict__)
			fhir_schema = self.fhir_object()

			response = requests.post(
				lafia_base_url + '/fhir/Task',
				json=fhir_schema, verify=False)
		
			task_object = response.json()
			frappe.errprint(task_object)

			if task_object.get("status") == 201:
				self.fhir_serverid = task_object.get("data")["id"]
		
			else:
				self.log_errors(response.__dict__)
				frappe.throw("An error occured")

	
	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/Task/' + self.fhir_serverid,
			json=fhir_schema, verify=False)
			
		task_object = response.json()
		print(task_object)

	def after_insert(self):
		event_body = {
			"resource_type": "Task",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.owner1,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def on_trash(self):
		response = requests.delete(
			lafia_base_url + '/fhir/Task/' + self.fhir_serverid, verify=False)		
		print(response.json())


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
