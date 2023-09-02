import requests
import json
import os, frappe
from frappe import whitelist
from datetime import timedelta
from dotenv import load_dotenv
from lafia.utils.fhir_utils import get_reference,format_datetime,get_code_list,\
    get_reference_list,get_fhir_doc,get_code
from frappe.utils import get_site_name,format_time,get_url,get_url_to_form,\
    cint,to_timedelta,get_time,time_diff_in_hours,get_datetime,get_weekday
from lafia.api.services.brokers.producer import producer

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")


def fhir_object(doc):
    end_time = to_timedelta(doc.appointment_time) + timedelta(minutes=cint(doc.duration))
    fhir_schema = {
        "resourceType": "Appointment",
        "status": set_status_(doc),
        "appointmentType": {"coding": [get_code("Appointment Types", doc.get("type"))]} if doc.get("type") else "",
        "participant": get_participant(doc),
        "comment": doc.notes,
        "created": format_datetime(doc.creation),
        "start": f'{doc.appointment_date}T{format_time(doc.appointment_time)}Z',
        "end": f'{doc.appointment_date}T{format_time(end_time)}Z',
        "minutesDuration":doc.duration,
        "serviceCategory": get_code_list("Healthcare Service Category", doc.get("service_category"), "category") if doc.get("service_category") else "",
        "reasonReference": get_reference_list("Condition",doc.get('reason'),'condition') if doc.get('reason') else [],
        "priority": doc.get("priority"),
        "slot": [get_slot(doc)]
    }
    print(fhir_schema)
    return fhir_schema

def get_slot(doc):
    schedule = frappe.get_doc("Healthcare Practitioner",doc.practitioner)\
                    .get('practitioner_schedules')[0].get("schedule")
    print(schedule)
    slots = frappe.get_doc("Practitioner Schedule",schedule).get('time_slots') if schedule else ""
    print(slots)
    weekday = get_weekday(get_datetime(doc.appointment_date))
    if slots:
        for slot in slots:
            if slot.get('day') == weekday and format_time(slot.get("from_time")) == format_time(doc.appointment_time):
                slot_id = slot.get('fhir_serverid')
                reference = {
                    "reference": f'Slot/{slot_id}'
                }
                print(reference)
                return reference


def before_insert(doc,method):
    if not doc.fhir_serverid:
        fhir_schema = fhir_object(doc)

        response = requests.post(
            lafia_base_url + '/Appointment', json=fhir_schema)
        
        app_object = response.json()
        print(app_object)
        
        if response.status_code == 201:
            doc.fhir_serverid = app_object.get("id")
        else:
            frappe.throw("An error occured")
            print(response.__dict__)

def on_update(doc, method):
    if doc.fhir_serverid:
        fhir_schema = fhir_object(doc)
        fhir_schema["id"] = doc.fhir_serverid
        
        url = lafia_base_url + '/Appointment/' + doc.fhir_serverid
        print(url)
        
        response = requests.put(
            url, json=fhir_schema)
        
        app_object = response.json()
        print(app_object)
        
    if doc.status == "Cancelled":
        create_appointment_response(doc,"Declined")

def on_delete(doc, method):
    response = requests.delete(
        lafia_base_url + '/Appointment/' + doc.fhir_serverid)
    
    print(response.json())

def after_save(doc, method):
    send_notification(doc)
    if doc.notification_sent:
        event_body = {
            "resource_type": "Appointment",
            "resource_id": doc.fhir_serverid,
            "data": {
                "practitioner": doc.practitioner,
                "patient": doc.patient,
                "provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
                "id": doc.fhir_serverid
            }
        }
        producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))

def set_status_(doc):
    resp = frappe.db.get_value("Appointment Response",{'appointment':doc.name},
                'name') if doc.name else ""
    
    if resp and (doc.status == "Scheduled" or doc.status == "Open"):
        return "booked"
    
    elif doc.status in ["","Scheduled","Open"]:
        return "pending"
    elif doc.status == "Closed":
        return "fulfilled"
    else:
        return "cancelled"
    
def get_participant(doc):
    app_response = frappe.db.get_value("Appointment Response",{'appointment':doc.name},'status') if doc.name else ""
    return [
        {
            "actor": get_reference("Patient",doc.patient),
            "required": "required",
            "status": "needs-action"
        },
        {
            "type": [ {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                    "code": "ATND",
                    "display": "attender"
                }]
            } ],
            "actor": get_reference("Healthcare Practitioner",doc.practitioner),
            "required": "required",
            "status": app_response.lower() if app_response else "needs-action"
        }
    ]

@whitelist(allow_guest=True)
def create_appointment(data):
    start = (data.get("start").replace("T", " ").replace("Z", "")).split(" ")
    end = (data.get("end").replace("T", " ").replace("Z", "")).split(" ")
    duration = cint(time_diff_in_hours(end[1],start[1])*60)
    patient = retrieve_participant(data).get('patient')
    company = frappe.db.get_value("Patient",{'name': patient},'organization')

    appointment_doc_data = {
        "doctype": "Patient Appointment",
        "fhir_serverid": data.get("id"),
        "type": data.get("type").get("coding")[0].get("display") if data.get("type") else "",
        "service_category": get_service_category(data) if data.get("service_category") else [],
        "reason": get_reason(data) if data.get("reason") else [],
        "priority": data.get("priority") if data.get("priority") else 0,
        "appointment_date": start[0],
        "appointment_time": start[1],
        "duration": duration,
        "notes": data.get('comment') if data.get('comment') else "", 
        "patient": patient,
        "practitioner": retrieve_participant(data).get('practitioner'),
        "company": company if company else frappe.defaults.get_user_default('company'),
        "notification_sent": 0,
        "mode_of_payment": "Suresalama",
        "docstatus": 0
    }
    appointment_doc = frappe.get_doc(appointment_doc_data)
    appointment_doc.insert()
    print('appointment created')
    frappe.db.commit()


def retrieve_participant(data):
    for participant in data.get("participant"):
        ref = participant.get("actor").get("reference").split("/")
        if ref[0] == "Patient":
            patient = get_fhir_doc("Patient",ref[1])
        else:
            practitioner = get_fhir_doc("Healthcare Practitioner",ref[1])
    return {'patient':patient,'practitioner':practitioner}



def get_service_category(data):
    category_list = []
    for category in data.get("service_category"):
        category_list.append({
            "category": category.get("coding")[0].get("display")
        })
    return category_list

def get_reason(data):
    reason_list = []
    for reason in data.get("reason"):
        split_reason = reason.get("reference").split("/")
        condition = get_fhir_doc("Condition",split_reason[1])
        if condition:
            reason_list.append({
                "condition": condition
            })
    return reason_list
    

def create_appointment_doc(data):
    response = requests.get(
        lafia_base_url + '/Appointment/' + data.get("id"))
    
    doc = response.json()
    print("doc")
    print(doc)
    fhir_data = {
        "id": doc["id"],
        "status": doc["status"],
        "type": doc["appointmentType"],
        "start": doc["start"],
        "end": doc["end"],
        "participant": doc["participant"],
        "service_category": doc["serviceCategory"],
        "reason": doc["reasonReference"],
        "priority": doc["priority"],
        "comment": doc["comment"] if doc["comment"] else ""
    }
    create_appointment(fhir_data)

@frappe.whitelist()
def create_appointment_response(doc,status):
    doc = json.loads(doc)
    response = check_response(doc.get('name'))
    if response:
        response_doc = frappe.get_doc("Appointment Response",response)
        response_doc.db_set("status", status, commit=True)
        response_doc.save()
    
    else:
        end_time = to_timedelta(doc.get('appointment_time')) + timedelta(minutes=cint(doc.get('duration')))
        appointment_date = doc.get('appointment_date')
        appointment_time = doc.get('appointment_time')
        
        response_doc_ = {
            "doctype": "Appointment Response",
            "appointment": doc.get('name'),
            "start": f'{appointment_date} {format_time(appointment_time)}',
            "end": f'{appointment_date} {format_time(get_time(end_time))}',
            "practitioner": doc.get('practitioner'),
            "practitioner_name": doc.get('practitioner_name'),
            "participant_type": [{
                "participant_type_code": "attender"
            }],
            "status": status,
            "docstatus": 0
        }
        response_doc = frappe.get_doc(response_doc_)
        response_doc.insert()
        frappe.db.commit()
        print("appointment response created")

@frappe.whitelist()
def check_response(name):
    return frappe.db.get_value("Appointment Response",{'appointment':name},'name')


def send_notification(doc):
    email = frappe.get_doc("Healthcare Practitioner",doc.practitioner).user_id
    args = {
        "practitioner": doc.practitioner_name,
        "patient": doc.patient,
        "user": email,
        "site_url": f"https://app.lafia.io/app/patient-appointment/{doc.name}",
        "date": doc.appointment_date,
        "time": doc.appointment_time
    }
    print(args)
    sender = frappe.session.user
    print(sender)
    # site_name = frappe.db.get_default("site_name") or frappe.get_conf().get("site_name")
    subject="Appointment Schedule"
    frappe.sendmail(
        recipients=[email],
        sender=sender,
        subject=subject,
        template="practitioner_appointment",
        args=args,
        header=[subject, "green"],
    )
    print("email sent")