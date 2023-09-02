from urllib import response
import frappe
import ssl
import certifi
from frappe.utils import get_site_name,getdate,get_date_str
from frappe.permissions import add_user_permission
from pprint import pprint
import sys
import requests
import json
import os
from dotenv import load_dotenv
from lafia.api.services.brokers.producer import producer
from lafia.utils.fhir_utils import get_identifier, get_period, get_telecom, get_fullname,ext_code_list,\
    random_string,get_contact,get_marital_status_code,get_addresses,retrieve_addresses,\
        get_code,get_codable,get_fhir_doc,get_reference
from lafia.api.users.users import sign_up
# from lafia.api.lake_fs.lake_fs import upload_object

load_dotenv()

lafia_base_url = os.environ.get("LAFIA_SERVER_URL")
lafia_system = os.environ.get("LAFIA_SYSTEM")


@frappe.whitelist()
def get_patient_info(email):
    try:
        patient = frappe.get_last_doc(
            doctype='Patient', filters={"email": email})
        return patient
    except:
        e = sys.exc_info()[1]
        frappe.local.response = frappe._dict({
            'status': 'error',
            'message': e
        })
        frappe.local.response['http_status_code'] = 500


def get_telecom_table(data):
    telecom_list = []
    for telecom in data:
        telecom_list.append({
            "use": telecom.get("use") if telecom.get("use") else "",
            "value": telecom.get("value") if telecom.get("value") else "",
            "system": telecom.get("system") if telecom.get("system") else "",
        })
    return telecom_list


@frappe.whitelist()
def create_patient(data):
    print(data)
    # if not frappe.get_all("Patient", data.get("full_name")):
    email = get_coms("email", data.get("telecom"))
    first_name =  data.get("name")[0].get("given")[0]
    last_name = data.get("name")[0].get("family")
    gender = data.get("gender").capitalize()
    birth_date = data.get("birthDate")
    patient_doc = frappe.get_doc({
        "doctype": "Patient",
        "fhir_serverid": data.get("id"),
        "notification_sent": 0,
        # "active": data.get("active"),
        "first_name": first_name,
        "last_name": last_name,
        "mobile": get_coms("phone", data.get("telecom")),
        "email": email,
        "sex": gender,
        "user_id": email,
        "dob": data.get("birthDate").replace("T", " ").replace("Z", "").split(" ")[0]
    })
    patient_doc.insert()
    frappe.db.commit()
    print("patient created")
    sign_up(email, first_name, last_name, data.get("patient_password"), gender, 'patient', ["Patient"], birth_date, patient_doc.mobile)
    print("Patient signup")
            

def get_coms(type, telecom):
    for com in telecom:
        if com.get("system") == type:
            value = com.get("value") if com.get("value") else ""
            return value


def get_relationship_code(relationship):
    return {
        "code": relationship.get("code"),
        "system": relationship.get("system"),
        "display": relationship.get("display")
    }


def get_patient_relationship(relationships):
    relationship_list = []
    for relationship in relationships:
        relationship_code = frappe.get_doc(
            'Relationship Code', relationship.get("relationship"))
        relationship_list.append({
            "coding": get_relationship_code(relationship_code),
            "text": relationship_code.get("display")
        })
    return relationship_list


def get_patient_contact(contacts):
    contact_list = []
    for contact in contacts:
        contact_list.append({
            "extension": [
                {
                    "url": f"{lafia_base_url}/StructureDefinition/LafiaContactMetadata",
                    "extension": [
                        {
                            "url": "birthDate",
                            "valueString": contact.get('birth_date')
                        },
                        {
                            "url": "maritalStatus",
                            "valueCodeableConcept": {
                            "coding": [get_code("Marital Status Code",contact.get('marital_status'))] if contact.get('marital_status') else []
                            }
                        }
                    ]
                }
            ],
            # "relationship": get_patient_relationship(patient_contact.get("relationship")) if patient_contact.get("relationship") else [],
            "name": {
                "use": "official",
                "text": contact.get('human_name'),
                "family": (contact.get('human_name').split(' '))[-1],
                "given": (contact.get('human_name').split(' '))
            },
            "gender": (contact.get("gender")).lower(),
            # "telecom": get_telecom(patient_contact.get("telecom")) if patient_contact.get("telecom") else [],
            "address": {
                "use": "home",
                "type": "physical",
                "line": [contact.get("address"),contact.get('postal_code')] if contact.get("address") else [],
                "city": contact.get("city") if contact.get("city") else '' ,
                "state": contact.get("state") if contact.get("state") else '',
                "country": contact.get("country") if contact.get("country") else '',
                "postalCode": contact.get('postal_code') if contact.get('postal_code') else ''
            }
            # "period": get_period(patient_contact.get("period")) if patient_contact.get("period") else ""
        })
    return contact_list

def fhir_object(doc):
    fhir_schema = {
        "resourceType": "Patient",
        "identifier": get_identifier(doc.get("identifier")) if doc.get("identifier") else [],
        "active": True,
        "name": get_fullname(doc.first_name, doc.last_name, doc.middle_name),
        "telecom": get_telecom(doc.get("email"), doc.get("mobile")),
        "gender": doc.sex.lower(),
        "birthDate": get_date_str(doc.dob) if doc.dob else "",
        "deceasedBoolean": False if doc.is_deaceased == 0 else True,
        "deceasedDatetime": get_date_str(doc.deaceased_date_time) if doc.deaceased_date_time else '',
        "address": get_addresses(doc.get("address")) if doc.address else "",
        "contact": get_patient_contact(doc.get("contact")) if doc.get("contact") else "",
        "maritalStatus": get_marital_status_code(doc.get("patient_marital_status")) if doc.get("patient_marital_status") else "",
        "extension": get_patient_extension(doc),
        "managingOrganization": get_reference("Company",doc.organization) if doc.organization else "",
        "generalPractitioner": general_practitioner(doc) if doc.practitioners else []
    }
    print(fhir_schema)
    return fhir_schema

def get_patient_extension(doc):
    extension_list = []
    
    extension_list.append({
        "url": f"{lafia_base_url}/StructureDefinition/lafiaCareTypesAndInterests",
        "valueCodeableConcept": {
            "coding": ext_code_list("Healthcare Service Specialty",doc.get('care_type'),'specialty')
        } if doc.get('care_type') else []
    }) 

    extension_list.append({
        "url": f"{lafia_base_url}/StructureDefinition/lafiaUserAnthropometry",
        "extension":[
            {
                "url": "height",
                "valueQuantity": {
                    "value": doc.height,
                    "unit": "ft",
                    "system": "http://unitsofmeasure.org",
                    "code": "ft_i"
                }
            },
            {
                "url": "weight",
                "valueQuantity": {
                    "value": doc.weight,
                    "unit": "kg",
                    "system": "http://unitsofmeasure.org",
                    "code": "kg"
                }
            }
        ]
    })
    
    assigner = frappe.db.get_value("Organization",{'name':"SureSalama"},'fhir_serverid')
    extension_list.append({
        "url": f"{lafia_base_url}/StructureDefinition/patient-insurance-provider",
        "valueIdentifier":{
            "value": doc.insurance_id,
            "system": lafia_system,
            "assigner": {"reference":f"Organization/{assigner}"} if assigner else ""
        }
    })

    if doc.patient_organization:
        for org in doc.patient_organization:
            org_id = frappe.db.get_value("Company",{'name':org.get('organization')},'fhir_serverid')
            extension_list.append({
                'url': f"{lafia_base_url}/StructureDefinition/patient-organization",
                "valueReference": {
                    "reference": f'Organization/{org_id}',
                    "type": "Organization"
                }
            })

    print(extension_list)
    return extension_list

def general_practitioner(doc):
    practitioner_list = []
    for practitioner in doc.get('practitioners'):
        practitioner_list.append(get_reference("Healthcare Practitioner",practitioner.get('practitioner')))
    
    return practitioner_list

def patient_lafia_before_insert_script(doc, method):
    print(doc.__dict__)
    if not doc.fhir_serverid:
        fhir_schema = fhir_object(doc)
        # fhir_schema['id'] = doc.get("uid")

        response = requests.post(
            lafia_base_url + '/Patient', json=fhir_schema)
        
        patient_fhir_object = response.json()
        print(patient_fhir_object)
        
        if response.status_code == 201:
            doc.fhir_serverid = patient_fhir_object["id"]
        else:
            frappe.throw("An error occured")
            print(response.__dict__)
            
def patient_on_update(doc, method):
    if doc.fhir_serverid:
        # frappe.errprint(doc.__dict__)
        fhir_schema = fhir_object(doc)
        fhir_schema["id"] = doc.fhir_serverid
        
        url = lafia_base_url + '/Patient/' + doc.fhir_serverid
        print(url)
        
        response = requests.put(
            url, json=fhir_schema, verify=False)
        
        patient_fhir_object = response.json()
        print(patient_fhir_object)
    
    if doc.user_id:
        print('here')
        add_customer_role_to_user(doc.user_id)

def patient_on_delete(doc, method):
    response = requests.delete(
        lafia_base_url + '/Patient/' + doc.fhir_serverid)
    
    print(response.json())

def get_email(telecom):
    email_addresses = []
    for comms in telecom:
        print('=loop==')
        print(comms.get("system"))
        if comms.get("system") == "email":
            email_addresses.append(comms.get("value"))
    return email_addresses


def get_phone(telecom):
    phone_numbers = []
    for comms in telecom:
        print('=loop==')
        print(comms.get("system"))
        if comms.get("system") == "phone":
            phone_numbers.append(comms.get("value"))
    return phone_numbers

def get_patient_doc(data):
    response = requests.get(
    lafia_base_url + '/Patient/' + data.get("id"), verify=False
    )
    doc = response.json()
    print(doc)
    fhir_data = {
        "id": doc["id"],
        "fullname": data.get("first_name") + " " + data.get("last_name"),
        "active": doc["active"],
        "name": doc["name"],
        "telecom": doc["telecom"],
        "gender": doc["gender"]
    }
    
    create_patient(fhir_data)

def patient_lafia_after_save(doc, method):
    if doc.notification_sent:
        last_name = doc.last_name
        first_name = doc.first_name
        password = random_string(15)

        event_body = {
            "resource_type": "patient",
            "resource_id": doc.fhir_serverid,
            "data": {
                "last_name": last_name,
                "first_name": first_name,
                "email": doc.email,
                "password": password,
                "gender": doc.sex,
                "provider": get_site_name(frappe.request.host if frappe.request else 'localhost'),
                "phone": doc.phone or doc.mobile,
                "organization_id": frappe.get_doc("Company",doc.organization).get('fhir_serverid') if doc.organization else ""
            }
        }
        
        # fhir_schema = fhir_object(doc)
        # file = ('_').join([doc.first_name,doc.last_name,doc.fhir_serverid])
        # upload_object(fhir_schema,"Patient",file)

        producer('{0}-createResources'.format(os.environ.get('SERVER_ENV')), json.dumps(event_body))
        if not doc.get("user_id"):
            sign_up(doc.email, first_name, last_name, password, doc.sex, 'patient', ["Patient"], doc.dob, doc.mobile)
            print("=========")
            user_doc = frappe.get_doc("User", doc.email)
            doc.user_id = user_doc.get("name")
            doc.save()

            create_patient_permission(doc)


def create_patient_permission(doc):
    patient_user_permission_exists = frappe.db.exists(
			"User Permission", {"allow": "Patient", "for_value": doc.name, "user": doc.user_id}
		)
    if patient_user_permission_exists:
        return
    
    add_user_permission("Patient",doc.name,doc.user_id)


def add_customer_role_to_user(user):
    if not frappe.get_all("Has Role", filters={"parent": user, "role": "Customer"}):
        frappe.get_doc({
            "doctype": "Has Role",
            "parenttype": "User",
            "parentfield": "roles",
            "parent": user,
            "role": "Customer"
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        print('added customer role')

def update_patient(data):
    name = frappe.db.get_value("Patient",{"fhir_serverid":data.get('id')},'name')
    if name:
        patient = frappe.get_doc("Patient",name)
        doc = patient_doc(data)
        patient.update(doc)
        patient.save()
        frappe.db.commit()
    return

def patient_doc(data):
    email = get_coms("email", data.get("telecom"))
    patient_doc_ = {
        # "fhir_serverid": data.get("id"),
        "first_name": data.get("name")[0].get("given")[0],
        # "middle_name": data.get("name")[0].get("given")[1] if data.get("name")[0].get("given")[1] else "",
        "last_name": data.get("name")[0].get("family"),
        "mobile": get_coms("phone", data.get("telecom")),
        "sex": data.get("gender").capitalize(),
        "patient_marital_status": get_codable(data,field="maritalStatus") if data.get("maritalStatus") else "",
        "dob": data.get("birthDate"),
        "address": retrieve_addresses(data.get("address")) if data.get("address") else [],
        "contact": retrieve_contact(data) if data.get("contact") else [],
        "is_deaceased": 0 if data.get("deceasedBoolean") == "false" else 1,
        "height": get_extension(data).get('height'),
        "weight": get_extension(data).get('weight'),
        "care_type": get_extension(data).get('care'),
        "insurance_id": get_extension(data).get('insurance_id'),
        "patient_organization": get_extension(data).get('organization'),
        "practitioners": get_general_practitioner(data) if data.get('generalPractitioner') else [],
        "docstatus": 0
    }
    print(patient_doc_)
    return patient_doc_

def retrieve_contact(data):
    return [{
        "human_name": data.get("contact")[0].get("name").get("text") if data.get("contact")[0].get("name") else "",
        "address": data.get("contact")[0].get("address").get("text") if data.get("contact")[0].get("address") else "",
        "city": data.get("contact")[0].get("address").get("city") if data.get("contact")[0].get("address") else "",
        "state": data.get("contact")[0].get("address").get("state") if data.get("contact")[0].get("address") else "",
        "country": data.get("contact")[0].get("address").get("country") if data.get("contact")[0].get("address") else "",
        "gender": (data.get("contact")[0].get("gender")).capitalize() if data.get("contact")[0].get("gender") else ""
        # "marital_status": data.get("contact")[0]
    }]

# def get_care_type(data):
#     care_list = []
#     for care in data.get("extension")[0].get("valueCodeableConcept").get("coding"):
#         care_list.append({
#             "specialty": care.get('display')
#         })
#     return(care_list)

def get_extension(data):
    ext_data = {}
    care_list = []
    height = 0
    weight = 0
    insurance_id = ""
    organizations = []
    for ext in data.get('extension'):
        if ext.get('url') == f"{lafia_base_url}/StructureDefinition/lafiaCareTypesAndInterests":
            for care in ext.get("valueCodeableConcept").get("coding"):
                care_list.append({
                    "specialty": care.get('display')
                })
        
        if ext.get('url') ==  f"{lafia_base_url}/StructureDefinition/lafiaUserAnthropometry":
            height += ext.get("extension")[0].get("valueQuantity").get("value")
            weight += ext.get("extension")[1].get("valueQuantity").get("value")
        
        if ext.get('url') == f"{lafia_base_url}/StructureDefinition/patient-insurance-provider":
            insurance_id += str(ext.get("valueIdentifier").get("value")) if ext.get("valueIdentifier").get("value") else ""

        if ext.get('url') == f"{lafia_base_url}/StructureDefinition/patient-organization":
            org_id = ext.get("valueReference").get('reference').split('/')[1]
            organizations.append({
                'organization': get_fhir_doc("Company",org_id)
            })

        ext_data['care'] = care_list
        ext_data['height'] = height
        ext_data['weight'] = weight
        ext_data['insurance_id'] = insurance_id
        ext_data['organization'] = organizations

    return ext_data


def get_general_practitioner(data):
    practitioner_list = []
    for practitioner in data.get('generalPractitioner'):
        id_ = practitioner.get('reference').split('/')[1]
        practitioner_list.append({
            'practitioner': get_fhir_doc("Healthcare Practitioner",id_)
        })
    
    return practitioner_list