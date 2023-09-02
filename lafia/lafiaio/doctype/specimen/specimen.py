# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe, requests, os,json
from frappe.model.document import Document
from lafia.utils.fhir_utils import get_identifier, get_code_list, get_reference,period, get_optional_doctype, get_reference_list, get_code,format_datetime,get_reference_table
from dotenv import load_dotenv
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

class Specimen(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType" : "Specimen",
			"identifier": get_identifier(self.identifier) if self.get("identifier") else "",
			"status": (self.get("status")).lower(),
			"type": {"coding": [get_code("Specimen Type", self.get("type"))]} if self.get("type") else [],
			"subject": get_reference(self.subject_type,self.subject),
			"receivedTime": format_datetime(self.get("received_time")) if self.get("received_time") else "",
			"parent": get_reference_list("Specimen",self.get('parent1'),'specimen') if self.get('parent1') else "",
			"request": get_reference_list("Service Request",self.get('request'),'service_request') if self.get('request') else "",
			"combined": (self.get("combined")).lower(),
			"role": get_code_list("Specimen Role", self.get("role"), "role") if self.get("role") else "",
			"feature": self.get_feature() if self.get("feature") else [],
			"collection": self.get_collection() if self.get("collection") else [],
			"processing": self.get_processing() if self.get("processing") else [],
			"container": self.get_container() if self.get("container") else [],
			"condition": get_code_list("Specimen Condition", self.get("condition"), "condition") if self.get("condition") else "",
			"note": {"text":self.note}			
		}
		print(fhir_schema)
		return fhir_schema


	def get_feature(self):
		feature_list = []
		for feature in self.get("feature"):
			feature_list.append({
				"type": {"coding": [get_code("Body Site Code", feature.get("type"))]},
				"description": feature.get("description")
			})
		return feature_list

	def get_collection(self):
		collection_list = []
		for collection in self.get("collection"):
			collection_list.append({
				"collector": get_reference(collection.get('collector_type'),collection.get('collector')),
				"collectedPeriod": period(collection.get('start_date'),collection.get('end_date')) if collection.get('start_date') and collection.get('end_date') else "",
				"quantity": {'value':collection.get("quantity"),'unit':collection.get('unit')},
				"method": {"coding": [get_code("Specimen Method", collection.get("collection_method"))]} if collection.get("collection_method") else "",
				"device": get_reference("Device",collection.get("device")) if collection.get("device") else "",
				"procedure": get_reference("Clinical Procedure",collection.get("procedure")) if collection.get("procedure") else "",
				"bodySite": {"coding": [get_code("Body Site Code", collection.get("body_site"))]} if collection.get("body_site") else "",
				"fastingStatusDuration": {'value':collection.get("fasting_status_duration")}
			})
		return collection_list

	def get_processing(self):
		processing_list = []
		for processing in self.get("processing"):
			processing_list.append({
				"description": processing.get("description"),
				"method": {"coding": [get_code("Specimen Processing Method", processing.get("method"))]} if processing.get("method") else "",
				"additive": [get_reference("Substance",processing.get("additive"))] if processing.get("additive") else [],
				"timePeriod": period(processing.get('start_date'),processing.get('end_date')) if processing.get('start_date') and processing.get('end_date') else ''
			})
		return processing_list


	def get_container(self):
		container_list = []
		for container in self.get("container"):
			container_list.append({
				"device": get_reference("Device",container.get("device")) if container.get("device") else "",
				"location": get_reference("Locations",container.get("location")) if container.get("location") else "",
				"specimenQuantity": {'value':container.get("quantity"),'unit':container.get('unit')}
			})
		return container_list

	
	def before_insert(self):
		if not self.fhir_serverid:
			fhir_schema = self.fhir_object()
			
			response = requests.post(
				lafia_base_url + '/fhir/Specimen', json=fhir_schema, verify=False)
			
			spec_object = response.json()
			frappe.errprint(spec_object)

			if spec_object.get("status") == 201:
				self.fhir_serverid = spec_object.get("data")["id"]
		
			else:
				frappe.throw("An error occured")
				print(response.__dict__)

	def on_update(self):
		fhir_schema = self.fhir_object()
		fhir_schema["id"] = self.fhir_serverid

		response = requests.put(
            lafia_base_url + '/fhir/Specimen/{0}'.format(self.fhir_serverid),
			json=fhir_schema, verify=False)
			
		spec_object = response.json()
		print(spec_object)
	
	def on_trash(self):
		response = requests.delete(
            lafia_base_url + '/fhir/Specimen/' + self.fhir_serverid, verify=False)
			
		print(response.json())
	
	def after_insert(self):
		event_body = {
			"resource_type": "Specimen",
        	"resource_id": self.fhir_serverid,
			"data": {
				"name": self.subject,
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": self.fhir_serverid
			}
		}
		producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

