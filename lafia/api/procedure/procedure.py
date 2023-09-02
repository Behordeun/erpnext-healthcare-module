from __future__ import unicode_literals
import frappe, requests, os, json
from lafia.utils.fhir_utils import get_identifier, get_code, get_code_list, get_reference,\
    get_optional_doctype, get_encounter, period, get_fhir_doc,get_practitioner
from dotenv import load_dotenv
from frappe import whitelist
from lafia.api.services.brokers.producer import producer
from frappe.utils import get_site_name,format_time

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


def fhir_object(doc):
    fhir_schema = {
        "resourceType": "Procedure",
        "identifier": get_identifier(doc.identifier) if doc.get("identifier") else "",
        # "basedOn": [get_reference(doc.get("basedon_type"), doc.get("basedon"))],
        # "partOf": [get_reference(doc.get("partof_type"), doc.get("partof"))],
        "statusReason":  {
            "coding": [get_code("Procedure Not Performed Reason Code", doc.get("statusreason"))]
            } if doc.get("statusreason") else "",
        "status": get_status(doc.get("status")),
        "category": {
            "coding": [get_code("Procedure Category Code", doc.get("category"))]
            } if doc.get("category") else "",
        "code": {
                "coding": [get_code("Procedure Code", doc.get("code"))]
            } if  doc.get("code") else "",
        "subject": get_reference("Patient", doc.get("patient")),
        "encounter": get_encounter(doc.encounter) if doc.encounter else "",
        "performedDateTime": f"{doc.start_date}T{format_time(doc.start_time)}Z",
        # "performedPeriod": period(doc.start_date,doc.end_date),
        # "performedString": doc.get("performedstring"),
        # "asserter": get_optional_doctype(doc.asserter_type, doc.asserter),
        "recorder": get_practitioner(doc.practitioner) if doc.practitioner else "",
        "performer": get_performer(doc.get("performer")) if doc.get("performer") else "",
        # "location": get_reference("Location FHIR", doc.location) if doc.location else "",
        "reasonCode": get_code_list("Procedure Reason Code Multi", doc.get("reasoncode"), "procedure_reason_code") if doc.get("reasoncode") else "",
        "bodySite": get_code_list("Body Site Multi", doc.get("bodysite"), "body_site_code") if doc.get("bodysite") else "",
        # "reasonReference": [get_optional_doctype(doc.reason_reference_type, doc.reason_reference)] if doc.get("reason_reference") else "",
        "outcome": {
            "coding": [get_code("Procedure Outcome Code", doc.get("outcome"))]
            } if doc.get("outcome") else "",
        # "report": [get_optional_doctype(report.get("report_type"), report.get("report")) for report in doc.get("report")] if doc.get("report") else "",
        "complication": get_code_list("Condition Code", doc.get("complication"), "condition") if doc.get("complication") else "",
        # "complicationDetail": get_reference_list("Condition", doc.get("complicationdetail"), "condition") if doc.get("complicationdetail") else "",
        # "followUp": get_code_list("Procedure Followup Code Multi", doc.get("followup"), "procedure_followup") if doc.get("followup") else "",
        "note": [
            {
                "text": doc.get("notes")
            }
        ] if doc.get("notes") else "",
        # "usedReference": [get_optional_doctype(reference.get("reference_type"), reference.get("reference")) for reference in doc.get("usedreference")] if doc.get("usedreference") else ""
        # "class": doc.get_class(doc.get("class")),

        # "period": get_period(doc.period)
    }
    print(fhir_schema)
    return fhir_schema

def procedure_before_insert(doc, method):
    if not doc.fhir_serverid:
        fhir_schema = fhir_object(doc)
        
        response = requests.post(
            lafia_base_url + '/Procedure', json=fhir_schema, verify=False)
        
        if not response.status_code == 201:
            print(response.__dict__)
            frappe.throw("An error occured")
        else:
            procedure_fhir_object = response.json()
            print(procedure_fhir_object)
            doc.fhir_serverid = procedure_fhir_object.get("id")

def procedure_before_save(doc,method):
    fhir_schema = fhir_object(doc)
    fhir_schema["id"] = doc.fhir_serverid

    response = requests.put(
        lafia_base_url + '/Procedure/' + doc.fhir_serverid,
        json=fhir_schema)
		
    procedure_object = response.json()
    print(procedure_object)

def on_delete(doc,method):
    response = requests.delete(
        lafia_base_url + '/Procedure/' + doc.fhir_serverid, verify=False)		
    print(response.json())


def procedure_after_insert(doc,method):
    if doc.notification_sent:
        event_body = {
            "resource_type": "Procedure",
            "resource_id": doc.fhir_serverid,
            "data": {
                "name": doc.name,
                "provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
                "id": doc.fhir_serverid
            }
        }
        producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))


def get_performer(performers):
    return [
        {
            "function":{
                "coding": [get_code("Performer Type", performer.get("function"))]
                } if performer.get("function") else "",
            "actor": get_reference(performer.get("actor_type"), performer.get("actor")),
            "onBehalfOf": get_reference("Organization", performer.get("on_behalf_of")) if performer.get("on_behalf_of") else ""
        } for performer in performers
    ]

def get_status(status):
    if status == "Draft":
        return "preparation"
    elif status == "Pending":
        return "on-hold"
    elif status == "In Progress":
        return "in-progress"
    elif status == "Cancelled":
        return "stopped"
    else:
        return "completed"


@frappe.whitelist()
def create_procedure(data):
    split_subject = data.get("subject").get("reference").split("/")
    split_encounter = data.get("encounter").get("reference").split("/") if data.get("encounter") else []
    date = (data.get("performedDateTime").replace("T", " ").replace("Z", "")).split(" ") if data.get("performedDateTime") else []
    split_performer = data.get("performer")[0].get("actor").get("reference").split("/") if data.get("performer") else []
    practitioner = get_fhir_doc("Healthcare Practitioner",split_performer[1]) if len(split_performer) > 1 else "",
    procedure_doc = {
        "doctype": "Clinical Procedure",
        "procedure_template": "Test",
        "fhir_serverid": data.get("id"),
        "statusreason": data.get("statusReason").get("coding")[0].get("display") if data.get("statusReason") else "",
        "category": data.get("category").get("coding")[0].get("display") if data.get("category") else "",
        "code": data.get("code").get("coding")[0].get("display") if data.get("code") else "",
        "patient": get_fhir_doc("Patient", split_subject[1]),
        "encounter": get_fhir_doc("Patient Encounter",split_encounter[1]) if len(split_encounter) > 1 else None,
        "start_date": date[0] if len(date) > 1 else "",
        "start_time": date[1] if len(date) > 1 else "",
        "practitioner": practitioner,
        "practitioner_name": frappe.get_doc("Healthcare Practitioner",practitioner).practitioner_name if practitioner else "",
        "performer": [{
                "actor_type":"Healthcare Practitioner",
                "actor": get_fhir_doc("Healthcare Practitioner",split_performer[1]) if len(split_performer) > 1 else "",
                "function": data.get("performer")[0].get("function").get("coding")[0].get("display") if data.get("performer")[0].get("function") else "",
                "on_behalf_of":""
        }] if data.get("performer") else [],
        "body_site": get_body_site(data) if data.get("bodySite") else [],
        "outcome": data.get("outcome").get("coding")[0].get("display") if data.get("outcome") else "",
        "complication": get_complication(data) if data.get("complication") else [],
        "notification_sent": 0,
        "docstatus": 1
    }
    doc = frappe.get_doc(procedure_doc)
    doc.insert()
    frappe.db.commit()
    print('procedure created')


def get_body_site(data):
    site_list = []
    for site in data.get("bodySite"):
        site_list.append({
            "body_site_code": site.get("coding")[0].get("display")
        })
    return site_list

def get_complication(data):
    comp_list = []
    for comp in data.get("complication"):
        comp_list.append({
            "condition": comp.get("coding")[0].get("display")
        })
    return comp_list