import frappe
import requests
import json
import os
from dotenv import load_dotenv
from lafia.api.services.brokers.producer import producer
from lafia.utils.fhir_utils import get_reference,get_telecom
from frappe.utils import get_site_name


load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


def fhir_object(doc):
    fhir_schema = {
        "resourceType": "Organization",
        "active": True,
        "type": [{"coding": [{
            "code":"prov",
            "system": "http://terminology.hl7.org/CodeSystem/organization-type",
            "display": "Healthcare Provider"
        }]}],
        "name": doc.company_name,
        "alias": [doc.abbr],
        "telecom": get_telecom(doc.get("email"), doc.get("phone_no")),
		"address": get_address(doc),
        # "partOf": get_reference("Company",doc.parent_company) if doc.parent_company else "",
        "extension": get_extension(doc)
    }
    print(fhir_schema)
    return fhir_schema

def before_insert(doc,method):
    if not doc.fhir_serverid:
        print(doc.__dict__)
        fhir_schema = fhir_object(doc)
        
        response = requests.post(
            lafia_base_url + '/Organization',
            json=fhir_schema)
    
        org_object = response.json()
        frappe.errprint(org_object)
    
        if response.status_code == 201:
            doc.fhir_serverid = org_object.get("id")
    
        else:
            frappe.throw("An error occured")

def on_update(doc,method):
    fhir_schema = fhir_object(doc)
    if doc.fhir_serverid:
        fhir_schema["id"] = doc.fhir_serverid

        response = requests.put(
            lafia_base_url + '/Organization/' + doc.fhir_serverid,
            json=fhir_schema)
            
        org_object = response.json()
        print(org_object)
    
    else:
        response = requests.post(
            lafia_base_url + '/Organization',
            json=fhir_schema)
    
        org_object = response.json()
        frappe.errprint(org_object)
    
        if response.status_code == 201:
            doc.db_set("fhir_serverid",org_object.get("id"),commit=True)
            doc.save()
    
        else:
            frappe.throw("An error occured")
        


def after_insert(doc,method):
    event_body = {
        "resource_type": "Organization",
        "resource_id": doc.fhir_serverid,
        "data": {
            "name": doc.company_name,
            "provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
            "id": doc.fhir_serverid
        }
    }
    producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

def on_trash(doc,method):
    response = requests.delete(
        lafia_base_url + '/Organization/' + doc.fhir_serverid)		
    print(response.json())


def get_extension(doc):
    extension_list = []
    extension_list.append({
        "url": f"{lafia_base_url}/StructureDefinition/organization-consulting-charge",
        "valueMoney": {
            "value": doc.consulting_charge,
            "currency": doc.default_currency
        }
    })
    extension_list.append({
        "url": f"{lafia_base_url}/StructureDefinition/organization-insurance-provider",
        "valueIdentifier":{
            "value": doc.insurance_id
        }
    })
    frappe.errprint(extension_list)
    return extension_list


def get_address(doc):
    name = doc.company_name
    address_list = []
    addresses = frappe.db.sql(f""" SELECT * FROM `tabAddress` WHERE name like '%{name}%' """,as_dict=1)
    if addresses:
        for address in addresses:
            address_list.append({
                "use": 'work' if address.get('address_type') == 'Office' else 'billing',
                "type": 'postal',
                "text": (address.get("address_line1")),
                "line": [address.get("address_line1"),address.get("pincode")],
                "city": address.get("city") if address.get("city") else '',
                "district": address.get("county") if address.get("county") else '',
                "state": address.get("state") if address.get("state") else '',
                "postalCode": address.get("pincode") if address.get("pincode") else '',
                "country": address.get("country") if address.get("country") else '',
            })
    return address_list

