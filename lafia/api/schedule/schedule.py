import sys
import requests
import json
import os, frappe
from frappe import whitelist
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier, get_reference,format_datetime
from frappe.utils import get_date_str,get_site_name,today,format_time
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")

def schedule_fhir_object(doc):
    prac_id = frappe.db.get_value("Healthcare Practitioner",
                        {'user_id': doc.owner},'fhir_serverid')
    fhir_schema = {
        "resourceType": "Schedule",
        "active": True if doc.disabled == 0 else False,
        # "name": doc.get('schedule_name'),
        "actor": [{"reference":f"Practitioner/{prac_id}"}]
    }
    print(fhir_schema)
    return fhir_schema

def before_insert(doc,method):
    if not (doc.owner).lower() == "administrator":
        schedules = frappe.get_list("Practitioner Schedule",filters={'owner':doc.owner})
        if schedules and frappe.session.user != 'Administrator':
            frappe.throw("You already have an enabled schedule")


    if not doc.fhir_serverid:
        fhir_schema = schedule_fhir_object(doc)

        response = requests.post(
            lafia_base_url + '/Schedule', json=fhir_schema)
        
        sch_object = response.json()
        print(sch_object)
        
        if response.status_code == 201:
            doc.fhir_serverid = sch_object.get("id")
        else:
            frappe.throw("An error occured")
            print(response.__dict__)


def validate(doc,method):
    if doc.get('time_slots'):
        for slot in doc.get('time_slots'):
            fhir_schema = {
                "resourceType": "Slot",
                "schedule": {"reference": f"Schedule/{doc.fhir_serverid}"},
                "status": 'free',
                "start": f"{today()}T{format_time(slot.get('from_time'))}Z",
                "end": f"{today()}T{format_time(slot.get('to_time'))}Z",
                "comment": slot.get('day')
            }

            if not slot.get('fhir_serverid'):
                response = requests.post(
                    lafia_base_url + '/Slot', json=fhir_schema)
                
                slot_object = response.json()
                print(slot_object)
                
                if response.status_code == 201:
                    slot.fhir_serverid = slot_object.get("id")
                else:
                    frappe.throw("An error occured")
                    print(response.__dict__)
                
                event_body = {
                    "resource_type": "Slot",
                    "resource_id": slot_object.get("id"),
                    "data": {
                        "provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
                        "id": slot_object.get("id")
                    }
                }
                producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

            else:
                fhir_schema["id"] = slot.get('fhir_serverid')

                response = requests.put(
                    lafia_base_url + '/Slot/' + slot.get('fhir_serverid'),
                    json=fhir_schema)
                    
                slot_object = response.json()
        frappe.db.commit()
    
    naming = custom_autoname(doc)
    return
   


def after_insert(doc,method):
    event_body = {
        "resource_type": "Schedule",
        "resource_id": doc.fhir_serverid,
        "data": {
            "name": doc.schedule_name,
            "provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
            "id": doc.fhir_serverid
        }
    }
    producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))
    update_practitioner_profile(doc)


def on_update(doc, method):
    fhir_schema = schedule_fhir_object(doc)
    fhir_schema["id"] = doc.fhir_serverid

    url = lafia_base_url + '/Schedule/' + doc.fhir_serverid
    response = requests.put(url, json=fhir_schema)    
    print(response.json())

    validate_slot(doc)
    

def on_trash(doc,method):
    if doc.fhir_serverid:
        response = requests.delete(
            lafia_base_url + '/Schedule/' + doc.fhir_serverid)
        
        print(response.json())

def custom_autoname(doc):
    doc.name = f"HLC-SCH-{doc.fhir_serverid}"


def validate_slot(doc):
    slots = frappe.get_all("Healthcare Schedule Time Slot",
                           filters={'parent':doc.name},pluck='fhir_serverid')
    if slots:
        response = requests.get(
                        lafia_base_url + '/Slot?schedule={0}&_count=100'.format(doc.fhir_serverid))
        
        if response.status_code == 200:
            slot_object = response.json()
            
            for slot in slot_object.get("entry"):
                slot_id = slot.get("resource").get("id")
                
                if slot_id not in slots:
                    delete_slot = requests.delete(
                                    lafia_base_url + '/Slot/' + slot_id)
                    print(delete_slot.json())
            

"""Updates Practitioner Profile with the created Schedule"""
def update_practitioner_profile(doc):
    if not (doc.owner).lower() == "administrator":
        practitioner = frappe.db.get_value("Healthcare Practitioner",
                        {'user_id': doc.owner},'name')
        print(practitioner)
        
        practitioner_doc = frappe.get_doc("Healthcare Practitioner",practitioner)
        practitioner_doc.practitioner_schedules = []
        practitioner_doc.update({
            'practitioner_schedules': [{
                'schedule': doc.name,
                'service_unit':frappe.db.get_value("Healthcare Service Unit",{
                                    'healthcare_service_unit_name':'General'},'name')
            }]
        })
        practitioner_doc.save()
        frappe.db.commit()

def check_service_unit(doc):
    company = frappe.defaults.get_user_default('company')
    service_unit = frappe.db.get_value("Healthcare Service Unit",{
        'healthcare_service_unit_name':'General','company':company},'name')
    if not service_unit:
        service_doc = frappe.get_doc({
            'doctype': "Healthcare Service Unit",
            'healthcare_service_unit_name':'General',
            'company':company,
            'service_unit_type': 'General',
            'parent_healthcare_service_unit': frappe.db.get_value("Healthcare Service Unit",{
                                        'healthcare_service_unit_name':'All Healthcare Service Units','company':company},'name'),
            'allow_appointments': 1,
            'service_unit_capacity': 2,
            'docstatus': 0
        }).insert(ignore_permissions=True, ignore_mandatory=True)
        frappe.db.commit()
        print(service_doc.get('name'))
        return service_doc.get('name')
    else:
        print(service_unit)
        return service_unit

