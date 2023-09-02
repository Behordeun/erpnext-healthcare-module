from __future__ import unicode_literals
from frappe.model.document import Document
import sys
import requests
import json
import os, frappe
from frappe import whitelist
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier,get_code_list,get_telecom,get_addresses,get_code,get_reference
from frappe.utils import get_date_str, get_site_name, get_datetime_str,get_time_str
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


def fhir_object(doc):
    fhir_schema = {
        "resourceType": "Location",
        "status": doc.status,
        "name": doc.healthcare_service_unit_name,
        "description": doc.description,
        "type": [{"text":doc.get("type")}],
        # "partOf": {"coding": [get_code("Location", doc.get("parent_healthcare_service_unit"))]} if doc.get("parent_healthcare_service_unit") else "",
        "physicalType": {"coding": [get_code("Location Type", doc.get("location_type"))]} if doc.get("location_type") else "",
        "managingOrganization": get_reference("Organization",doc.provider) if doc.provider else "",
        "hoursOfOperation": hours_of_operation(doc.get('hours_of_operation')) if doc.get('hours_of_operation') else ""
        }
    return fhir_schema

def hours_of_operation(operations):
    operation_list = []
    for operation in operations:
        operation_list.append({
            "daysOfWeek": [operation.get('weeks')],
            "allDay": True if operation.get('days') == 1 else False,
            "openingTime": get_time_str(operation.get('openingtime')) if operation.get('openingtime') else '',
            "closingTime": get_time_str(operation.get('closingtime')) if operation.get('closingtime') else '',
        })
    return operation_list

def before_insert(doc,method):
    if not doc.fhir_serverid:
        print(doc.__dict__)
        fhir_schema = fhir_object(doc)
        
        response = requests.post(
            lafia_base_url + '/Location',
            json=fhir_schema, verify=False)
    
        location_object = response.json()
        frappe.errprint(location_object)
    
        if location_object.get("status") == 201:
            doc.fhir_serverid = location_object.get("data")["id"]
    
        else:
            frappe.throw("An error occured")

def on_update(doc,method):
    fhir_schema = fhir_object(doc)
    fhir_schema["id"] = doc.fhir_serverid

    response = requests.put(
        lafia_base_url + '/Location/' + doc.fhir_serverid,
        json=fhir_schema, verify=False)
        
    location_object = response.json()
    print(location_object)

def after_insert(doc,method):
    event_body = {
        "resource_type": "Location",
        "resource_id": doc.fhir_serverid,
        "data": {
            "name": doc.healthcare_service_unit_name,
            "provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
            "id": doc.fhir_serverid
        }
    }
    producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

def on_trash(doc,method):
    response = requests.delete(
        lafia_base_url + '/Location/' + doc.fhir_serverid, verify=False)		
    print(response.json())