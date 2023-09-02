import sys
import requests
import json
import os, frappe
from frappe import whitelist
from lafia.api.services.brokers.producer import producer
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_identifier, get_code, get_period,get_fhir_doc, get_practitioner, get_reference
from frappe.utils import get_date_str, get_site_name

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


@whitelist(allow_guest=True)
def create_encounter(encounter_data):
  split_subject = encounter_data.get("subject").get("reference").split("/")
  split_participant = encounter_data.get("participant")[0].get("individual").get("reference").split("/")
  period = (encounter_data.get("period").get("start").replace("T", " ").replace("Z", "")).split(" ")
  patient = get_fhir_doc("Patient", split_subject[1])
  company = frappe.db.get_value("Patient",{'name': patient},'organization')
  
  encounter_doc_data = {
    "doctype": "Patient Encounter",
    "type": encounter_data.get("type").get("coding")[0].get("display") if encounter_data.get("type") else "",
    "class": encounter_data.get("class").get("display"),
    "status": encounter_data.get("status").capitalize(),
    "patient": patient,
    "practitioner": get_fhir_doc("Healthcare Practitioner",split_participant[1]),
    "encounter_date": period[0],
    "encounter_time": period[1],
    "encounter_end_date": encounter_data.get("period").get("end").replace("T", " ").replace("Z", "") if encounter_data.get("period").get("end") else "",
    "reason": encounter_data.get("reasonCode")[0].get("text") if encounter_data.get("reasonCode") else "",
    "fhir_serverid": encounter_data.get("id"),
    "company": company if company else frappe.defaults.get_user_default('company'),
    "notification_sent": 0,
    "docstatus": 1
  }
  encounter_doc = frappe.get_doc(encounter_doc_data)
  encounter_doc.insert()
#   encounter_doc.submit()
  print('encounter created')
  frappe.db.commit()

  print(encounter_doc)


def encounter_before_insert_script(doc, method):
	print(doc.__dict__)
	if not doc.fhir_serverid:
		# provider = frappe.get_doc("Organization", doc.get("service_provider"))
		fhir_schema = fhir_object(doc)
		fhir_schema["id"]: doc.uid
		print(f'fhir_schema : {fhir_schema}')
		
		response = requests.post(
            lafia_base_url + '/Encounter', json=fhir_schema)
		
		encounter_object = response.json()
		frappe.errprint(encounter_object)
		
		if response.status_code == 201:
			doc.fhir_serverid = encounter_object.get("id")
		
		else:
			frappe.throw("An error occured")
			frappe.errprint(response.__dict__)


def encounter_on_update(doc, method):
	fhir_schema = fhir_object(doc)
	fhir_schema["id"] = doc.fhir_serverid

	response = requests.put(
		lafia_base_url + '/Encounter/' + doc.fhir_serverid,
		json=fhir_schema)
		
	encounter_object = response.json()
	print(encounter_object)

		
def fhir_object(doc):
	fhir_schema = {
		"resourceType": "Encounter",
		"identifier": get_identifier(doc.get("identifier")) if doc.get("identifier") else [],
		"status": doc.get("statuss").lower() if doc.get("statuss") else '',
		"class": get_class(doc.get("class")) if doc.get("class") else "",
		"subject": get_subject(doc.patient) if doc.get("patient") else "",
		"participant": all_participants(doc.practitioner, doc.get("participants")) if doc.get("practitioner") else "",
		"type": [{"coding": [get_code("Encounter Type Code", doc.get("type"))]}] if doc.get("type") else "",
		"period": {"start": doc.get("encounter_date")},
		"reasonCode": [{"text": doc.get("reason") if doc.reason else ""}],
		"serviceProvider": get_reference("Organization",doc.get("service_provider")) if doc.get("service_provider") else "",
		"priority":{"coding": [get_code("Priority Code", doc.get("priority"))] if doc.get("priority") else [] },
		"diagnosis": {
			"condition": {"display" : doc.get("diagnosis") if doc.diagnosis else ""}
		},
		"location": get_location(doc.get("location")) if doc.get("location") else []
	}
	return fhir_schema



def get_class(class_display):
		class_doc = frappe.get_doc("Encounter Class Code", class_display)
		return {
			"system": class_doc.get("system"),
			"code": class_doc.get("code"),
			"display": class_doc.get("display")
		}

def get_subject(subject):
		reference = None
		patient_doc = frappe.get_doc("Patient", subject)
		reference = "Patient/" + patient_doc.get("fhir_serverid")
		return {
			"reference": reference
		}

def retrieve_subject(subject):
	patient = frappe.db.get_value("Patient", {"fhir_serverid":subject.get("id")}, "name")
	return patient

def get_participants(participants):
		participant_list = []
		for participant in participants:
			obj = {
				"type": [
					{
						"coding": [get_code("Participant Type Code", participant.get("type"))]
					}
				],
				"individual": get_practitioner(participant.get("individual")) if participant.get("individual_type") == "Healthcare Practitioner" \
					else get_reference(participant.get("individual_type"),participant.get("individual")),
				"period": get_period([{
					"start": get_date_str(participant.get("from_period")) if participant.get("from_period") else '',
					"end": get_date_str(participant.get("to_period")) if participant.get("to_period") else ''
				}])
			}
			participant_list.append(obj)
		return participant_list

def all_participants(practitioner, participants):
	all_participant = []
	h_prac = {
		"type": [{"coding":[{"display":"admitter"}]}],
		"individual": get_practitioner(practitioner)
	}
	all_participant.append(h_prac)
	prac_list = get_participants(participants) if participants else ''
	all_participant.extend(prac_list)
	
	return all_participant



def get_location(locations):
	location_list = []
	for location in locations:
		loc = {
			"location": {
				"display": location.get("location")
			},
			"status": location.get("status").lower(),
			"physicalType": {
				"coding": [get_code("Location Type",location.get("physical_type"))]
			}
		}
		location_list.append(loc)
	return location_list

def get_encounter_doc(data):
	response = requests.get(lafia_base_url + '/Encounter/' + data.get("id"))
	fhir_encounter = response.json()
	doc = fhir_encounter.get("data")
	print("fhir_encounter")
	print(fhir_encounter)
	print(doc)
	fhir_data = {
		"id": doc["id"],
		"status": doc["status"],
		"type": doc["type"],
		"class": doc["class"],
		"subject": doc["subject"],
		"participant": doc["participant"],
		"period": doc["period"],
		"reasonCode": doc["reasonCode"]
	}
	return fhir_data

def encounter_after_save(doc, method):
	if doc.notification_sent:
		event_body = {
			"resource_type": "Encounter",
			"resource_id": doc.fhir_serverid,
			"data": {
				"provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
				"id": doc.fhir_serverid
			}
		}
		print(event_body)
		produced_encounter = producer('{0}-createResources'.format(os.environ.get("SERVER_ENV")), json.dumps(event_body))
		print("=========")
		doc.save()

def on_trash(doc,method):
    response = requests.delete(
        lafia_base_url + '/Encounter/' + doc.fhir_serverid)		
    print(response.json())