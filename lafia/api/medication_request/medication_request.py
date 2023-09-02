import frappe, os
from lafia.utils.fhir_utils import get_fhir_doc
from dotenv import load_dotenv
load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


def create_medication_request(data):
    split_subject = data.get("subject").get("reference").split("/")
    split_encounter = data.get("encounter").get("reference").split("/") if data.get("encounter") else []
    split_requester = data.get("requester").get("reference").split("/") if data.get("requester") else []
    split_performer = data.get("performer").get("reference").split("/") if data.get("performer") else []
    request_doc = {
        "doctype": "Medication Request",
        "fhir_serverid": data.get("id"),
        "status": data.get("status").capitalize(),
        "intent": data.get("intent").capitalize() if data.get("intent") else "",
        "subject": get_fhir_doc("Patient", split_subject[1]),
        "encounter": get_fhir_doc("Patient Encounter",split_encounter[1]) if len(split_encounter) > 1 else None,
        "date": data.get("authoredOn").replace("T", " ").replace("Z", "") if data.get("authoredOn") else "",
        "requester_ref": "Healthcare Practitioner" if len(split_requester) > 1 and split_requester[0] == "Practitioner" else "",
        "requester": get_fhir_doc("Healthcare Practitioner",split_requester[1]) if len(split_requester) > 1 and split_requester[0] == "Practitioner" else "",
        "medication": data.get("medicationCodeableConcept").get("coding")[0].get("display") if data.get("medicationCodeableConcept") else "",
        "reason_code": get_reason_code(data) if data.get("reasonCode") else [],
        "performer_ref": "Healthcare Practitioner" if len(split_performer) > 1 and split_performer[0] == "Practitioner" else "",
        "performer": get_fhir_doc("Healthcare Practitioner",split_performer[1]) if len(split_performer) > 1 and split_performer[0] == "Practitioner" else "",
        "dosage_instruction": get_dosage(data) if data.get("dosageInstruction") else [],
        "notification_sent": 0,
        "docstatus": 0   
    }
    doc = frappe.get_doc(request_doc)
    doc.insert()
    frappe.db.commit()
    print('medication request created')

def get_reason_code(data):
    reason_list = []
    for reason in data.get("reasonCode"):
        reason_list.append({
            "condition": reason.get("coding")[0].get("display")
        })
    return reason_list

def get_dosage(data):
    dosage_list = []
    for dosage in data.get("dosageInstruction"):
        dosage_list.append({
            "text": dosage.get("text")
        })
    return dosage_list