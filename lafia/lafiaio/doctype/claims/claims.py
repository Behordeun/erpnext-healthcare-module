# -*- coding: utf-8 -*-
# Copyright (c) 2021, ParallelScore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.document import Document
import sys
import requests
import json
import os, frappe
from frappe import whitelist
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier, get_code, get_period, get_reference, get_fhir_doc, get_practitioner,format_datetime
from frappe.utils import get_date_str, get_site_name, get_datetime_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


class Claims(Document):
	def fhir_object(self):
		fhir_schema = {
			"resourceType": "Claim",
			"identifier": get_identifier(self.get("identifier")) if self.get("identifier") else [],
			"status": (self.code).lower(),
			"type": {"coding": [get_code("Claim Type", self.get("type"))]} if self.get("type") else "",
			"subType": [{"coding": [get_code("Claim Subtype", self.get("sub_type"))]}] if self.get("sub_type") else "",
			"use": self.use.lower() if self.use else '',
			"patient": get_reference("Patient",self.patient),
			"billablePeriod": {'start':format_datetime(self.billable_start), 'end':format_datetime(self.billable_end)} if self.billable_start else '',
			"created": format_datetime(self.created),
			"enterer": get_practitioner(self.author) if self.author else '',
			"insurer": get_reference("Organization",self.insurer) if self.insurer else '',
			"provider": get_practitioner(self.provider) if self.provider else '',
			"priority": {"coding": [get_code("Process Priority", self.get("priority"))]} if self.priority else '',
			"fundsReserve": get_codable(self.funds_reserve) if self.funds_reserve else '',
			"related": get_related_claim(self.get('related')) if self.get('related') else '',
			"prescription": get_reference(self.get("prescription")[0].get("ref_type"), self.get("prescription")[0].get("ref_name")) if self.get("prescription") else '',
			"originalPrescription": get_reference(self.get("original_prescription")[0].get("ref_type"), self.get("original_prescription")[0].get("ref_name")) if self.get("original_prescription") else '',
			"payee": {
				"type": {"coding": [get_code("Payee Type", self.get("payee_type"))]} if self.get("payee_type") else "",
				"party": get_reference(self.recipient_type,self.recipient)
			} if self.get("payee") else '',
			"careTeam": get_care_team(self.get("care_team")) if self.get("care_team") else '',
			"diagnosis": get_diagnosis(self.get("diagnosis")) if self.get("diagnosis") else '',
			"procedure": get_procedure(self.get("procedure")) if self.get("procedure") else '',
			"insurance": get_insurance(self.get("insurance")) if self.get("insurance") else ''
		}
		print(fhir_schema)
		return fhir_schema
	

	# def before_insert(self):
	# 	if not self.fhir_serverid:
	# 		fhir_schema = self.fhir_object()
	# 		fhir_schema["id"] = self.uid
			
	# 		response = requests.post(
	# 			lafia_base_url + '/Claim', json=fhir_schema)
			
	# 		claim_object = response.json()
	# 		frappe.errprint(claim_object)

	# 		if response.status_code == 201:
	# 			self.fhir_serverid = claim_object.get("id")
		
	# 		else:
	# 			frappe.throw("An error occured")
	# 			print(response.__dict__)

	# def before_save(self):
	# 	fhir_schema = self.fhir_object()
	# 	fhir_schema["id"] = self.fhir_serverid

	# 	response = requests.put(
    #         lafia_base_url + '/Claim/{0}'.format(self.fhir_serverid),
	# 		json=fhir_schema)
			
	# 	claim_object = response.json()
	# 	print(claim_object)
	
	# def on_trash(self):
	# 	fhir_schema = self.fhir_object()
	# 	fhir_schema["id"] = self.fhir_serverid

	# 	response = requests.delete(
    #         lafia_base_url + '/Claim/' + self.fhir_serverid,
	# 		json=fhir_schema)
			
	# 	claim_object = response.json()
	# 	print(claim_object)
	
	# def after_insert(self):
	# 	event_body = {
	# 		"resource_type": "Claim",
    #     	"resource_id": self.fhir_serverid,
	# 		"data": {
	# 			"provider": get_site_name(frappe.request.host if frappe.request else 'localhost')
	# 		}
	# 	}
	# 	producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

	
@whitelist(allow_guest=True)
def create_claims(data):
    split_patient = data.get("patient").get("reference").split("/")
    split_enterer = data.get("enterer").get("reference").split("/")
    split_provider = data.get("provider").get("reference").split("/") if data.get("provider") else ""
    split_insurer = data.get("insurer").get("reference").split("/")
    patient = get_fhir_doc("Patient",split_patient[1])
    company = frappe.db.get_value("Patient",{'name': patient},'organization')
    claims_doc_data = {
        "doctype": "Claims",
        "fhir_serverid": data.get("id"),
        "status": data.get("status").capitalize() if data.get("status") else "Active",
		"patient": patient,
        "type": data.get("type").get("coding")[0].get("display") if data.get("type") else "",
        "use": data.get("use").capitalize() if data.get("use") else "",
		# "sub_type": data.get("sub_type").get("coding")[0].get("display") if data.get("sub_type") else "",
        "created": data.get("created").replace("T", " ").replace("Z", ""),
		"author": get_fhir_doc("Healthcare Practitioner",split_enterer[1]),
        "provider": get_fhir_doc("Healthcare Practitioner",split_provider[1]),
		"insurer": get_fhir_doc("Organization",split_insurer[1]),
		"billable_start": data.get("billablePeriod").get("start").replace("T", " ").replace("Z", "") if data.get("billablePeriod").get("start") else "",
		"billable_end": data.get("billablePeriod").get("end").replace("T", " ").replace("Z", "") if data.get("billablePeriod").get("end") else "",
        "priority": data.get("priority").get("coding")[0].get("display") if data.get("priority") else "",
		"insurance": retrieve_insurance(data) if data.get("insurance") else [],
		"payee_type": data.get("payee").get("type").get("coding")[0].get("display") if data.get("payee").get("type") else "",
		"company": company if company else frappe.defaults.get_user_default('company'),
		"docstatus": 1
    }
    claim_doc = frappe.get_doc(claims_doc_data)
    claim_doc.insert()
    print('claims created')
    frappe.db.commit()


def get_claims_doc(data):
    response = requests.get(
    lafia_base_url + '/Claim/' + data.get("id"), verify=False
    )
    doc = response.json()
    # doc = fhir_claims.get("data")
    print("fhir_claims")
    # print(fhir_claims)
    print(doc)
    fhir_data = {
		"id": doc["id"],
		"status": doc["status"],
		"patient": doc["patient"],
		"type": doc["type"],
		"use": doc["use"],
		# "sub_type": doc["subType"],
		"created" : doc["created"],
		"enterer": doc["enterer"],
		"provider": doc["provider"],
		"priority": doc["priority"],
		"insurer": doc["insurer"],
		"billable_period": doc["billablePeriod"],
		"insurance": doc["insurance"]
    }
    create_claims(fhir_data)

def get_priority(priority):
    for i in priority.get("coding"):
        return i.get("code").capitalize()

def get_codable(code):
	return {
		'coding':[{
			'display': code
		}]
	}

def get_related_claim(claims):
	claim_list = []
	for i in claims:
		claim_list.append({
			"claim": get_reference("Claims",i.get('claim')),
			"relationship": get_codable(i.get("relationship"))
		})
	return claim_list

def get_care_team(teams):
	team_list = []
	for team in teams:
		team_list.append({
			"sequence": team.get('sequence') if  team.get('sequence') else 1,
			"provider": get_reference(team.get('provider'),team.get('provider_name')) if team.get('provider') else '',
			"responsible": True if team.get('responsible') == 1 else False,
			"role": get_codable(team.get("role")) if team.get("role") else ''
		})
	return team_list

def get_diagnosis(diagnosis):
	diagnosis_list = []
	for diag in diagnosis:
		diagnosis_list.append({
			"sequence": diag.get('sequence') if diag.get('sequence') else 1,
			"diagnosisReference": get_reference("Condition",diag.get('diagnosis_reference')) if diag.get('diagnosis_reference') else '',
			"type": [get_codable(diag.get('type'))] if diag.get('type') else '',
			"onAdmission": get_codable(diag.get("on_admission")) if diag.get("on_admission") else ''
		})
	return diagnosis_list

def get_procedure(procedures):
	procedure_list = []
	for procedure in procedures:
		procedure_list.append({
			"sequence": procedure.get('sequence') if procedure.get('sequence') else 1,
			"type": [get_codable(procedure.get('type'))] if procedure.get('type') else '',
			"date": get_date_str(procedure.get('date')) if procedure.get('date') else '',
			"procedureReference": get_reference("Procedure",procedure.get("procedure_reference")) if procedure.get("procedure_reference") else '',
			"udi": [get_reference("Device",procedure.get("udi"))] if procedure.get("udi") else ''
		})
	return procedure_list

def get_insurance(insurances):
	insurance_list = []
	for insurance in insurances:
		insurance_list.append({
			"sequence": insurance.get('sequence') if insurance.get('sequence') else 1,
			"focal": True if insurance.get('focal') == 1 else False,
			# "identifier": {'value': insurance.get('value')} if insurance.get('value') else '',
			"coverage": get_reference("Coverage", insurance.get("coverage")) if insurance.get("coverage") else '',
			# "businessArrangement": insurance.get('business_arrangement'),
			# "preAuthRef": insurance.get('preauthref'),
			# "claimResponse": get_reference("ClaimResponse",insurance.get("claim_response")) if insurance.get("claim_response") else ''
		})
	return insurance_list


def retrieve_insurance(data):
	insurance_list = []
	for insurance in data.get("insurance"):
		split_coverage = insurance.get("coverage").get("reference").split("/") if insurance.get("coverage") else ""
		insurance_list.append({
			"sequence": insurance.get('sequence') if insurance.get('sequence') else 1,
			"focal": 1 if insurance.get('focal') == "true" else 0,
			"coverage": get_fhir_doc("Coverage",split_coverage[1]) if len(split_coverage) > 1 else "",
			})
	return insurance_list

