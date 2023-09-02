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



class ClaimResponse(Document):
	pass


@whitelist(allow_guest=True)
def create_claim_response(data):
    split_patient = data.get("patient").get("reference").split("/")
    split_requestor = data.get("requestor").get("reference").split("/")
    split_insurer = data.get("insurer").get("reference").split("/") if data.get("insurer") else []
    split_request = data.get("request").get("reference").split("/")
    claims_doc_data = {
        "doctype": "ClaimResponse",
        "fhir_serverid": data.get("id"),
		"identifier": retrieve_identifier(data) if data.get("identifier") else [],
        "status": data.get("status").capitalize() if data.get("status") else "Active",
		"patient": get_fhir_doc("Patient",split_patient[1]),
        "type": data.get("type").get("coding")[0].get("display") if data.get("type") else "",
        "use": data.get("use").capitalize() if data.get("use") else "",
		"created": data.get("created").replace("T", " ").replace("Z", ""),
		"requestor": get_fhir_doc("Healthcare Practitioner",split_requestor[1]),
		"request": get_fhir_doc("Claims",split_request[1]),
		"outcome": data.get("outcome").capitalize() if data.get("outcome") else "",
		"disposition": data.get("disposition"),
		"insurer": get_fhir_doc("Organization",split_insurer[1]) if split_insurer else "",
		"total": get_total(data) if data.get("total") else [],
		"insurance": retrieve_insurance(data) if data.get("insurance") else [],
		"payee_type": data.get("payeeType").get("coding")[0].get("display") if data.get("payeeType") else "",
		"docstatus": 0
    }
    claim_doc = frappe.get_doc(claims_doc_data)
    claim_doc.insert()
    print('claims created')
    frappe.db.commit()

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

def retrieve_identifier(data):
	identifier_list = []
	for iden in data.get("identifier"):
		split_assigner = iden.get("assigner").get("reference").split("/") if iden.get("assigner") else []
		identifier_list.append({
			"use": iden.get("use").capitalize() if iden.get("use") else "",
			"type": iden.get("type").get("coding")[0].get("display") if iden.get("type") else "",
			"system": iden.get("system") if iden.get("system") else "",
			"assigner": get_fhir_doc("Organization",split_assigner[1]) if split_assigner else ""
		})
	return identifier_list

def get_total(data):
	total_list = []
	for total in data.get("total"):
		total_list.append({
			"category": total.get("category").get("coding")[0].get("display") if total.get("category") else "",
			"amount": total.get("amount").get("value") if total.get("amount") else ""
		})
	return total_list

