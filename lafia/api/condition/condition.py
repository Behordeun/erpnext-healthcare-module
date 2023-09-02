import frappe
from lafia.utils.fhir_utils import get_fhir_doc

@frappe.whitelist()
def create_condition_request(data):
    split_subject = data.get("subject").get("reference").split("/")
    split_encounter = data.get("encounter").get("reference").split("/") if data.get("encounter") else []
    split_recorder = data.get("recorder").get("reference").split("/") if data.get("recorder") else []
    patient = get_fhir_doc("Patient", split_subject[1])
    company = frappe.db.get_value("Patient",{'name': patient},'organization')
    condition_doc = {
        "doctype": "Condition",
        # "subject":
        "fhir_serverid": data.get("id"),
        "status": data.get("clinicalStatus").get("coding")[0].get("display") if data.get("clinicalStatus") else "Active",
        "verification_status": data.get("verificationStatus").get("coding")[0].get("display") if data.get("verificationStatus") else "Unconfirmed",
        "category": (data.get("category")[0].get("coding")[0].get("display")).capitalize() if data.get("category") else "",
        "severity": data.get("severity").get("coding")[0].get("display") if data.get("severity") else "Moderate",
        "code": data.get("code").get("coding")[0].get("display") if data.get("code") else "",
        "body_site": get_body_site(data) if data.get("bodySite") else [],
        "patient": patient,
        "encounter": get_fhir_doc("Patient Encounter",split_encounter[1]) if len(split_encounter) > 1 else None,
        "recorded_date": data.get("recordedDate").replace("T", " ").replace("Z", "") if data.get("recordedDate") else "",
        "recorder_ref": "Healthcare Practitioner" if len(split_recorder) > 1 and split_recorder[0] == "Practitioner" else "Patient",
        "recorder": get_fhir_doc("Healthcare Practitioner",split_recorder[1]) if len(split_recorder) > 1 and split_recorder[0] == "Practitioner" else get_fhir_doc("Patient", split_subject[1]),
        "note": [{
            "time": data.get("note")[0].get("time").replace("T", " ").replace("Z", "") if data.get("note")[0].get("time") else "",
            "text": data.get("note")[0].get("text")
        }] if data.get("note") else [],
        "notification_sent": 0,
        "company": company if company else frappe.defaults.get_user_default('company'),
        "docstatus": 1
    }
    doc = frappe.get_doc(condition_doc)
    doc.insert()
    frappe.db.commit()
    print("condition created")

def get_body_site(data):
    site_list = []
    for site in data.get("bodySite"):
        site_list.append({
            "body_site_code": site.get("coding")[0].get("display")
        })
    return site_list