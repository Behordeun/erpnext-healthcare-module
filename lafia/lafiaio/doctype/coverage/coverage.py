# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from frappe.model.document import Document
import frappe
import sys
import requests
import json
import os
from dotenv import load_dotenv
from frappe import whitelist, _
from lafia.api.services.brokers.producer import producer
from lafia.utils.fhir_utils import get_identifier, get_code,get_reference,get_reference_table,\
	format_datetime,get_fhir_doc
from lafia.api.users.users import sign_up
from frappe.utils import get_site_name

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


class Coverage(Document):
	# def before_insert(self):
	# 	if not self.fhir_serverid:
	# 		fhir_schema = self.fhir_object()	
			
	# 		response = requests.post(
	# 			lafia_base_url + '/Coverage', json=fhir_schema)
			
	# 		cov_fhir_object = response.json()
	# 		print(cov_fhir_object)
			
	# 		if response.status_code == 201:
	# 			self.fhir_serverid = cov_fhir_object.get("id")
			
	# 		else:
	# 			frappe.throw("An error occured")
	# 			print(response.__dict__)

	def set_title(self):
		self.title = _('{0} with {1}').format(self.subscriber,
			self.beneficiary)[:100]
		
	def validate(self):
		self.set_title()

	# def on_update(self):
	# 	fhir_schema = self.fhir_object()
	# 	fhir_schema["id"] = self.fhir_serverid

	# 	response = requests.put(
    #         lafia_base_url + '/Coverage/' + self.fhir_serverid,
	# 		json=fhir_schema)
			
	# 	cov_object = response.json()
	# 	print(cov_object)

	
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Coverage",
			"identifier": get_identifier(self.get("identifier")) if self.get("identifier") else [],
			"status": self.get('status').lower(),
			"kind": self.get("kind").lower(),
			"paymentBy": self.get_paymentby() if self.get("payment_by") else [],
			"type" : {"coding": [get_code("Coverage Type", self.get("type"))]} if self.get("type") else "",
			"policyHolder": get_reference(self.policy_holder_type,self.policy_holder) if self.policy_holder_type else '',
			"subscriber": get_reference("Patient",self.subscriber) if self.subscriber else '',
			# "subscriberId": self.uid,
			"beneficiary": get_reference("Patient",self.beneficiary) if self.beneficiary else '',
			"dependent": self.get("dependent"),
			"relationship": {"coding": [get_code("Subscriber Relationship", self.get("relationship"))]} if self.get("relationship") else '',
			"period": {'start':format_datetime(self.start_date), 'end':format_datetime(self.end_date)},
			"insurer": get_reference("Organization",self.insurer) if self.insurer else "",
			"payor": get_reference_table(self.get('payor')) if self.get('payor') else [],
			"class": get_class(self.get("class")) if self.get("class") else '',
			"costToBeneficiary": self.get_cost() if self.get('cost_to_beneficiary') else []
		}
		return fhir_schema


	
	# def after_insert(self):
	# 	event_body = {
	# 		"resource_type": "Coverage",
    #     	"resource_id": self.fhir_serverid,
	# 		"data": {
	# 			"name": self.name,
	# 			"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
	# 			"id": self.fhir_serverid
	# 		}
	# 	}
	# 	producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	def get_paymentby(self):
		payment_list = []
		for payment in self.get("payment_by"):
			payment_list.append({
				"party": get_reference(payment.get('party_type'),payment.get('party')),
				"responsibility": payment.get("responsibility")
			})
		return payment_list
	
	def get_cost(self):
		cost_list = []
		for cost in self.get('cost_to_beneficiary'):
			cost_list.append({
				"type": {"coding": [get_code("Coverage Copay Type", cost.get("type"))]} if cost.get("type") else "",
				"valueMoney": {
					"value":cost.get("value_money"),
					"currency": frappe.get_doc("Company",self.company).get('default_currency') if self.company else ""
				}
			})
		return cost_list
	
def get_class(classes):
	class_list = []
	for cls in classes:
		class_list.append({
			"type": {"coding": [get_code("Coverage Class", cls.get("type"))]} if cls.get("type") else "",
			"value": cls.get("value"),
			"name": cls.get("name1")
		})
	return class_list


def get_coverage(data):
	response = requests.get(
		lafia_base_url + '/Coverage/' + data.get("id"))

	fhir_cov = response.json()
	doc = fhir_cov.get("data")
	print("fhir_cov")
	print(fhir_cov)
	print(doc)
	fhir_data = {
		"id": doc["id"],
		"status": doc["status"],
		"type": doc["type"],
		"subscriber": doc["subscriber"],
		"beneficiary": doc["beneficiary"],
		"dependent": doc["dependent"],
		"relationship": doc["relationship"],
		"period": doc["period"],
		"class": doc["class"],
		"cost_to_beneficiary": doc["costToBeneficiary"],
		"payor": doc["payor"]
	}
	create_coverage(fhir_data)

def create_coverage(data):
	split_subscriber = data.get("subscriber").get("reference").split("/")
	split_beneficiary = data.get("beneficiary").get("reference").split("/")
	patient = get_fhir_doc("Patient",split_subscriber[1])
	company = frappe.db.get_value("Patient",{'name': patient},'organization')
	coverage_data = {
		"doctype": "Coverage",
		"fhir_serverid": data.get("id"),
        "status": data.get("status").capitalize() if data.get("status") else "Active",
        "type": data.get("type").get("coding")[0].get("display") if data.get("type") else "",
        "subscriber": patient,
		"beneficiary": get_fhir_doc("Patient",split_beneficiary[1]),
		"dependent": data.get("dependent"),
		"relationship": data.get("relationship").get("coding")[0].get("display") if data.get("relationship") else "",
		"start_date": data.get("period").get("start").replace("T", " ").replace("Z", "") if data.get("period").get("start") else "",
		"end_date": data.get("period").get("end").replace("T", " ").replace("Z", "") if data.get("period").get("end") else "",
		"payor": get_payor(data) if data.get('payor') else [],
		"class": retrieve_class(data) if data.get("class") else [],
		"cost_to_beneficiary": retrieve_cost(data) if data.get("costToBeneficiary") else [],
		"company": company if company else frappe.defaults.get_user_default('company'),
		"docstatus": 1
	}
	coverage_doc = frappe.get_doc(coverage_data)
	coverage_doc.insert()
	frappe.db.commit()
	print('coverage created')

def get_payor(data):
	payor_list = []
	for payor in data.get('payor'):
		ref = payor.get("reference").split("/")
		doct = ref[0].capitalize()
		payor_list.append({
			"ref_type": doct,
			"ref_name": get_fhir_doc(doct,ref[1])
		})
	return payor_list

def retrieve_class(data):
	class_list = []
	for cls in data.get("class"):
		class_list.append({
			"type": cls.get("type").get("coding")[0].get("display") if cls.get("type") else "",
			"value": cls.get('value') if cls.get('value') else "",
			"name1": cls.get('name') if cls.get('name') else ""
		})
	return class_list

def retrieve_cost(data):
	cost_list = []
	for cost in data.get("costToBeneficiary"):
		cost_list.append({
			"type": cost.get("type").get("coding")[0].get("display") if cost.get("type") else "",
			"value_money": cost.get("valueMoney").get('value') if cost.get("valueMoney") else "",
			"value_quantity": "",
			"exception": ""
		})
	return cost_list